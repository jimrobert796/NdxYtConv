from fastapi import HTTPException, FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from pathlib import Path
import uvicorn

# Importar el core
from core.downloader import YouTubeDownloaderCore, VideoInfo



# Inicializar templates y app
templates = Jinja2Templates(directory="templates")
app = FastAPI()


# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Inicializar el core
downloader = YouTubeDownloaderCore()



# Función para limpieza en background
def borrar_archivo(path: Path):
    """Elimina archivo de forma segura"""
    try:
        if path and path.exists():
            path.unlink()
    except Exception as e:
        print(f"Error borrando {path}: {e}")

@app.get('/')
def index(req: Request):
    return templates.TemplateResponse(
        name="index.html",
        context={"request": req}
    )

@app.get("/request")
def obtener_info_video(urlVideo: str):
    """
    Obtiene información del video usando el core
    """
    try:
        video_info = downloader.get_video_info(urlVideo)
        return {
            "success": True,
            "thumbnail": video_info.thumbnail_url,
            "titulo": video_info.title,
            "canal": video_info.author,
            "video_id": video_info.video_id,
            "duracion": video_info.duration,
            "views": video_info.views,
            "length_formatted": video_info.length_formatted,
            "thumbnail_type": "maxresdefault" if "maxresdefault" in video_info.thumbnail_url else "hqdefault"
        }
        
    except Exception as e:
        print(f"Error obteniendo info: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"URL inválida o error: {str(e)}"
        )

@app.get("/conversion/mp3")
def convertir_mp3(url: str, background_tasks: BackgroundTasks):
    """
    ## 🎵 Convertir YouTube a MP3 usando el core
    
    ### 📋 Cómo probar en Swagger:
    1. 👆 Haz clic en **"Try it out"**
    2. 📝 Pega una URL de YouTube:
    3. 🎯 Haz clic en **"Execute"**
    4. ⬇️ El navegador **descargará automáticamente** el MP3
    """
    try:
        # Usar el core para descargar
        output_path = downloader.download_mp3(url)
        
        # Agregar tarea para limpiar después
        background_tasks.add_task(borrar_archivo, output_path)
        
        return FileResponse(
            output_path,
            media_type="audio/mpeg",
            filename=output_path.name
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error descargando MP3: {str(e)}"
        )

@app.get("/conversion/mp4")
def convertir_mp4(url: str, calidad: int, background_tasks: BackgroundTasks):
    """
    ## 🎬 Convertir YouTube a MP4 con Calidad Seleccionable usando el core
    
    ### 📋 Cómo probar en Swagger:
    1. 👆 Haz clic en **"Try it out"**
    2. 📝 **Pega una URL de YouTube:**
    3. 🎯 **Selecciona calidad (1-5):**
       - **1** = 144p (Calidad baja, archivo pequeño)
       - **2** = 360p (Calidad estándar)
       - **3** = 720p (HD - Alta definición)
       - **4** = 1080p (Full HD - Muy buena calidad)
       - **5** = Máxima resolución disponible
    4. ⚡ Haz clic en **"Execute"**
    5. ⬇️ **El navegador descargará automáticamente** el MP4
    """
    try:
        # Validar calidad
        if calidad not in [1, 2, 3, 4, 5]:
            raise HTTPException(status_code=400, detail="Calidad inválida. Use 1-5")
        
        # Usar el core para descargar
        output_path = downloader.download_mp4(url, calidad)
        
        # Agregar tarea para limpiar después
        background_tasks.add_task(borrar_archivo, output_path)
        
        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename=output_path.name
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error descargando MP4: {str(e)}"
        )

@app.post("/debug/streams")
def debug_streams(url: str):
    """
    Debug endpoint para ver streams disponibles
    """
    try:
        streams = downloader.get_available_streams(url)
        
        print("\n===== STREAMS DISPONIBLES =====\n")
        for stream in streams:
            print(
                f"itag={stream['itag']} | "
                f"type={stream['mime_type']} | "
                f"res={stream['resolution']} | "
                f"abr={stream['abr']} | "
                f"audio={stream['has_audio']}"
            )
        print("\n===== FIN =====\n")
        
        return {"status": "Revisa la terminal", "count": len(streams)}
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error obteniendo streams: {str(e)}"
        )

@app.on_event("shutdown")
def cleanup_on_shutdown():
    """
    Limpiar archivos temporales al cerrar la aplicación
    """
    downloader.cleanup()


if __name__ == "__main__":
    uvicorn.run("main:app")