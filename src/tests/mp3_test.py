from pytubefix import *
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB

from io import BytesIO  # Para enviar el archivo como flujo de bytes

from typing import Union

import requests

from fastapi import HTTPException, FastAPI, Form
from fastapi.responses import FileResponse

import subprocess
import uuid
import os

app = FastAPI()

# /request
# Hace un request sobre la informacion del video para ser usada




@app.get("/request")
def leerUrl(urlVideo: str):
    try:
        # 1. Crear objeto YouTube
        yt = YouTube(urlVideo)
        
        # 2. Construir URL de maxresdefault
        maxresThumbUrl = f"https://i.ytimg.com/vi/{yt.video_id}/maxresdefault.jpg"
        print(f"Intentando miniatura: {maxresThumbUrl}")
        
        # 3. Intentar obtener la miniatura maxresdefault
        response = requests.get(maxresThumbUrl, timeout=5)
        print(f"Status code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        
        # 4. DECISIÓN: ¿Usar maxresdefault o fallback?
        if response.status_code == 200:
            print("✅ Miniatura maxresdefault encontrada")
            thumbnail_url = maxresThumbUrl  # Usar maxresdefault
        else:
            print("❌ No hay miniatura maxresdefault, usando hqdefault")
            # Usar hqdefault (siempre disponible)
            thumbnail_url = f"https://i.ytimg.com/vi/{yt.video_id}/hqdefault.jpg"
        
        # 5. Retornar la información
        return {
            "success": True,
            "thumbnail": thumbnail_url,
            "titulo": yt.title,
            "canal": yt.author,
            "video_id": yt.video_id,
            "duracion": yt.length,
            "views": yt.views,
            "thumbnail_type": "maxresdefault" if "maxresdefault" in thumbnail_url else "hqdefault"
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail=f"URL inválida o error: {str(e)}"
        )



# Notas:
# falta aun poner el album o imagen a el mp3

@app.post("/conversion/mp3")
def convertir_mp3(url: str = Form(...)):
    """
    ## 🎵 Convertir YouTube a MP3 (PARA PRUEBAS)

    **ESTE ENDPOINT ES IDEAL PARA PRUEBAS** porque:
    - ✅ Descarga directa en Swagger
    - ✅ No requiere endpoints adicionales
    - ✅ Streaming inmediato
    - ✅ Fácil de probar

    ### 📋 Cómo probar en Swagger:
    1. 👆 Haz clic en **"Try it out"**
    2. 📝 Pega una URL de YouTube:
    ```
    https://www.youtube.com/watch?v=dQw4w9WgXcQ
    ```
    3. 🎯 Haz clic en **"Execute"**
    4. ⬇️ El navegador **descargará automáticamente** el MP3

    ### 🎬 Ejemplos para probar:
    ```json
    // Música popular
    {"url": "https://youtu.be/p8IZoTQLpXQ"}

    ### ⚠️ Notas importantes:
    - Usa videos **CORTOS** (1-5 minutos) para pruebas rápidas
    - Asegúrate de que el video sea **público**
    - La primera prueba puede tardar unos segundos
    """

    try:
        print("Verificando url")
        yt = YouTube(url)
        
        # Lista de thumbnails en orden de preferencia
        thumbnail_candidates = [
            f"https://i.ytimg.com/vi/{yt.video_id}/maxresdefault.jpg",  # Máxima calidad
            f"https://i.ytimg.com/vi/{yt.video_id}/sddefault.jpg",      # Alta calidad
            f"https://i.ytimg.com/vi/{yt.video_id}/hqdefault.jpg",      # Buena calidad
        ]
        
        thumbnail_data = None
        thumbnail_url_used = None
        
        # Intentar descargar thumbnail
        for thumbnail_url in thumbnail_candidates:
            try:
                print(f"  Probando: {thumbnail_url}")
                response = requests.get(thumbnail_url, timeout=5)
                
                if response.status_code == 200 and 'image' in response.headers.get('content-type', ''):
                    thumbnail_data = response.content
                    thumbnail_url_used = thumbnail_url
                    print(f"  ✅ Thumbnail encontrada: {thumbnail_url.split('/')[-1]}")
                    break
                    
            except Exception as e:
                print(f"  ❌ Error con {thumbnail_url.split('/')[-1]}: {e}")
                continue
        
        # Si no se encontró thumbnail, usar el de pytube
        if not thumbnail_data:
            try:
                thumbnail_url_used = yt.thumbnail_url
                response = requests.get(thumbnail_url_used, timeout=5)
                if response.status_code == 200:
                    thumbnail_data = response.content
                    print("  ✅ Usando thumbnail de pytube")
            except:
                print("  ⚠️ No se pudo obtener thumbnail")
                thumbnail_data = None
        
        
        audio = yt.streams.get_audio_only()

        os.makedirs("temp", exist_ok=True)

        print("Creando ruta temporal")
        temp_filename = f"{uuid.uuid4()}.webm"
        mp3_filename = temp_filename.replace(".webm", ".mp3")

        temp_path = f"temp/{temp_filename}"
        mp3_path = f"temp/{mp3_filename}"

        print("Descargando audio")
        audio.download(output_path="temp", filename=temp_filename)

        # Conviertiendo de M4a a Mp3
        print("Conviertiendo de M4a a Mp3")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", temp_path,
            "-vn",
            "-ab", "192k",
            mp3_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Preparando para METADATOS
        mp3 = MP3(mp3_path, ID3=ID3)
        if mp3.tags is None:
            mp3.add_tags()

        print("Aplicando estructura de METADATOS")
        # Aplicando estructura
        mp3.tags.add(TIT2(encoding=3, text=yt.title))  # Nombre
        mp3.tags.add(TPE1(encoding=3, text=yt.author))  # Autor
        mp3.tags.add(TALB(encoding=3, text="YouTube"))  # Album
        
        if thumbnail_data:
                try:
                    # Determinar tipo MIME de la imagen
                    content_type = response.headers.get('content-type', 'image/jpeg')
                    mime_type = 'image/jpeg' if 'jpeg' in content_type or 'jpg' in content_type else 'image/png'
                    
                    # Añadir imagen como carátula
                    mp3.tags.add(APIC(
                        encoding=3,                 # UTF-8
                        mime=mime_type,            # Tipo MIME
                        type=3,                     # 3 = carátula frontal
                        desc='Cover',               # Descripción
                        data=thumbnail_data         # Datos de la imagen
                    ))
                    print("✅ Thumbnail añadida como carátula")
                    
                except Exception as e:
                    print(f"⚠️ Error añadiendo thumbnail: {e}")
            
            # Guardar metadatos
                mp3.save(v2_version=3)  # Usar ID3v2.3 para mejor compatibilidad
                print("✅ Metadatos guardados")
        

        # Retornamos en forma de descarga para uso
        print("MP3 listo para la descarga")
        return FileResponse(
            mp3_path,
            media_type="audio/mpeg",
            filename=f"{yt.title}.mp3"

        )

    except Exception as e:
        raise HTTPException(status_code=400, detail="Error f{e}")




@app.post("/debug/streams")
def debug_streams(url: str = Form(...)):
    yt = YouTube(url)

    print("\n===== STREAMS DISPONIBLES =====\n")

    for stream in yt.streams:
        #if(stream.includes_audio_track == True):  OPCIONAL PARA VISTA
                
            print(
                f"itag={stream.itag} | "
                f"type={stream.mime_type} | "
                f"res={stream.resolution} | "
                f"abr={stream.abr} | "
                f"audio={stream.includes_audio_track}"
            )

    print("\n===== FIN =====\n")

    return {"status": "Revisa la terminal"}

@app.post("/conversion/mp4")
def convertir_mp4(url: str = Form(...), calidad: int = Form(...)):
    try:
        yt = YouTube(url)
        os.makedirs("temp", exist_ok=True)

        # 🔹 AUDIO (siempre)
        audio = yt.streams.get_by_itag(140)
        if not audio:
            raise HTTPException(status_code=404, detail="Audio no disponible")

        audio_path = f"temp/{uuid.uuid4()}.m4a"
        audio.download(output_path="temp", filename=os.path.basename(audio_path))

        # 🔹 VIDEO
        match calidad:
            case 1:  # 144p
                video = yt.streams.filter(res="144p", mime_type="video/mp4").first()
            case 2:  # 360p
                video = yt.streams.filter(res="360p", mime_type="video/mp4").first()
            case 3:  # 720p
                video = yt.streams.filter(res="720p", mime_type="video/mp4").first()
            case 4:  # 1080p
                video = yt.streams.filter(res="1080p", mime_type="video/mp4").first()
            case 5:  # máxima
                video = yt.streams.filter(mime_type="video/mp4").order_by("resolution").desc().first()
            case _:
                raise HTTPException(status_code=400, detail="Calidad inválida")

        if not video:
            raise HTTPException(status_code=404, detail="Video no disponible")

        video_path = f"temp/{uuid.uuid4()}.mp4"
        video.download(output_path="temp", filename=os.path.basename(video_path))

        # 🔗 UNIR AUDIO + VIDEO
        final_path = f"temp/{uuid.uuid4()}.mp4"

        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            final_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return FileResponse(
            final_path,
            media_type="video/mp4",
            filename=f"{yt.title}.mp4"
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
