#!/usr/bin/env python3
"""
YouTube Downloader - Versión Terminal con ventana "Guardar como"
Descarga videos y audio de YouTube desde la línea de comandos
"""

import os
import sys
import argparse
import subprocess
import webbrowser
import json
from pathlib import Path
import platform

# Verificar e instalar dependencias automáticamente
def verificar_dependencias():
    """Verifica e instala dependencias necesarias"""
    dependencias = ['pytubefix', 'mutagen', 'requests']
    
    print("🔍 Verificando dependencias...")
    
    for dependencia in dependencias:
        try:
            __import__(dependencia.replace('-', '_'))
            print(f"   ✅ {dependencia}")
        except ImportError:
            print(f"   ⚠️  {dependencia} no encontrada, instalando...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dependencia])
                print(f"   ✅ {dependencia} instalada")
            except:
                print(f"   ❌ Error instalando {dependencia}")
                return False
    
    # Verificar ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("   ✅ ffmpeg")
    except:
        print("   ⚠️  ffmpeg no encontrado")
        print("   ℹ️  Para instalar ffmpeg:")
        print("      Ubuntu/Debian: sudo apt install ffmpeg")
        print("      macOS: brew install ffmpeg")
        print("      Windows: Descargar de https://ffmpeg.org/")
    
    return True


# Si hay dependencias faltantes, intentar instalarlas
if __name__ == "__main__":
    if not verificar_dependencias():
        sys.exit(1)

# Ahora importamos las dependencias
from pytubefix import YouTube
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
import requests
import uuid
import shutil


class YouTubeDownloaderCLI:
    """Clase principal para el descargador de YouTube en terminal"""
    
    def __init__(self):
        self.temp_dir = Path("temp_youtube")
        self.temp_dir.mkdir(exist_ok=True)
        self.descargas_dir = Path("Descargas_YouTube")
        self.descargas_dir.mkdir(exist_ok=True)
        
        # Configuración
        self.config_file = Path("yt_downloader_config.json")
        self.cargar_configuracion()
    
    def cargar_configuracion(self):
        """Carga la configuración desde archivo"""
        config_default = {
            "ubicacion_descargas": str(self.descargas_dir.absolute()),
            "abrir_carpeta_despues": True,
            "preguntar_ubicacion": True
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                # Asegurar que todas las claves existan
                for key in config_default:
                    if key not in self.config:
                        self.config[key] = config_default[key]
            except:
                self.config = config_default
        else:
            self.config = config_default
        
        self.descargas_dir = Path(self.config["ubicacion_descargas"])
        self.descargas_dir.mkdir(exist_ok=True)
    
    def guardar_configuracion(self):
        """Guarda la configuración en archivo"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def mostrar_banner(self):
        """Muestra el banner de la aplicación"""
        banner = """
╔══════════════════════════════════════════════════════════╗
║      🎬 YOUTUBE DOWNLOADER - VENTANA GUARDAR COMO 🎵     ║
║         Descarga y selecciona dónde guardar archivos     ║
╚══════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def obtener_ubicacion_guardado(self, nombre_archivo, extension):
        """Pregunta al usuario dónde guardar el archivo"""
        sistema = platform.system()
        
        print(f"\n📂 Selecciona dónde guardar '{nombre_archivo}{extension}':")
        print("=" * 60)
        
        # Opciones predefinidas
        opciones = [
            ("1", "Carpeta actual", Path.cwd()),
            ("2", "Carpeta Descargas_YouTube", self.descargas_dir),
            ("3", "Carpeta Descargas del sistema", self.obtener_carpeta_descargas()),
            ("4", "Especificar otra carpeta", None),
            ("5", "Seleccionar con explorador de archivos", "explorador")
        ]
        
        for num, nombre, ruta in opciones:
            if ruta and isinstance(ruta, Path):
                print(f"   {num}. {nombre}")
                print(f"      📍 {ruta.absolute()}")
            else:
                print(f"   {num}. {nombre}")
        
        print("=" * 60)
        
        while True:
            eleccion = input("\n📝 Selecciona una opción (1-5): ").strip()
            
            if eleccion == "1":
                return Path.cwd()
            elif eleccion == "2":
                return self.descargas_dir
            elif eleccion == "3":
                return self.obtener_carpeta_descargas()
            elif eleccion == "4":
                return self.pedir_ruta_manual()
            elif eleccion == "5":
                return self.abrir_explorador_archivos(nombre_archivo, extension)
            else:
                print("❌ Opción inválida. Intenta de nuevo.")
    
    def obtener_carpeta_descargas(self):
        """Obtiene la carpeta de descargas del sistema"""
        sistema = platform.system()
        
        if sistema == "Windows":
            downloads = Path.home() / "Downloads"
        elif sistema == "Darwin":  # macOS
            downloads = Path.home() / "Downloads"
        elif sistema == "Linux":
            downloads = Path.home() / "Downloads"
        else:
            downloads = Path.cwd()
        
        downloads.mkdir(exist_ok=True)
        return downloads
    
    def pedir_ruta_manual(self):
        """Pide al usuario que ingrese una ruta manualmente"""
        while True:
            ruta_str = input("\n📁 Ingresa la ruta completa de la carpeta: ").strip()
            
            if not ruta_str:
                print("⚠️  La ruta no puede estar vacía")
                continue
            
            ruta = Path(ruta_str)
            
            # Expandir ~ para el directorio home
            if ruta_str.startswith("~"):
                ruta = Path.home() / ruta_str[2:]
            
            if not ruta.exists():
                crear = input(f"⚠️  La carpeta no existe. ¿Crear '{ruta}'? (s/n): ").lower()
                if crear == 's':
                    try:
                        ruta.mkdir(parents=True, exist_ok=True)
                        print(f"✅ Carpeta creada: {ruta.absolute()}")
                        return ruta
                    except Exception as e:
                        print(f"❌ Error creando carpeta: {e}")
                        continue
                else:
                    continue
            
            if not ruta.is_dir():
                print("❌ La ruta debe ser una carpeta, no un archivo")
                continue
            
            return ruta
    
    def abrir_explorador_archivos(self, nombre_archivo, extension):
        """Abre el explorador de archivos del sistema"""
        sistema = platform.system()
        archivo_sugerido = f"{nombre_archivo}{extension}"
        
        print(f"\n📂 Se abrirá el explorador de archivos...")
        print(f"   Nombre sugerido: {archivo_sugerido}")
        
        if sistema == "Windows":
            # En Windows, usamos tkinter para diálogo de guardar
            try:
                import tkinter as tk
                from tkinter import filedialog
                
                root = tk.Tk()
                root.withdraw()  # Ocultar ventana principal
                
                archivo = filedialog.asksaveasfilename(
                    defaultextension=extension,
                    initialfile=nombre_archivo,
                    title="Guardar archivo como",
                    filetypes=[(f"{extension.upper()} files", f"*{extension}"), ("All files", "*.*")]
                )
                
                if archivo:
                    ruta_guardado = Path(archivo).parent
                    nombre_final = Path(archivo).name
                    print(f"✅ Seleccionado: {ruta_guardado.absolute()}/{nombre_final}")
                    return ruta_guardado, nombre_final
                else:
                    print("⚠️  No se seleccionó ubicación, usando carpeta actual")
                    return Path.cwd(), archivo_sugerido
                    
            except ImportError:
                print("⚠️  Tkinter no disponible, usando carpeta actual")
                return Path.cwd(), archivo_sugerido
        
        elif sistema == "Darwin":  # macOS
            # En macOS, podemos usar AppleScript
            try:
                script = f'''
                set theFile to choose file name with prompt "Guardar como {archivo_sugerido}" default name "{archivo_sugerido}"
                POSIX path of theFile
                '''
                result = subprocess.run(['osascript', '-e', script], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    ruta_completa = Path(result.stdout.strip())
                    return ruta_completa.parent, ruta_completa.name
            except:
                pass
            
            print("⚠️  No se pudo abrir diálogo nativo, usando carpeta actual")
            return Path.cwd(), archivo_sugerido
        
        else:  # Linux
            # En Linux, intentamos con zenity o kdialog
            try:
                # Probar zenity (Gnome)
                result = subprocess.run([
                    'zenity', '--file-selection', '--save',
                    '--title', f'Guardar {archivo_sugerido}',
                    '--filename', archivo_sugerido
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    ruta_completa = Path(result.stdout.strip())
                    return ruta_completa.parent, ruta_completa.name
            except:
                try:
                    # Probar kdialog (KDE)
                    result = subprocess.run([
                        'kdialog', '--getsavefilename',
                        archivo_sugerido,
                        f'*.{extension.lstrip(".")}'
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        ruta_completa = Path(result.stdout.strip())
                        return ruta_completa.parent, ruta_completa.name
                except:
                    pass
            
            print("⚠️  No se pudo abrir diálogo nativo, usando carpeta actual")
            return Path.cwd(), archivo_sugerido
    
    def abrir_carpeta(self, ruta):
        """Abre la carpeta en el explorador de archivos"""
        sistema = platform.system()
        
        try:
            if sistema == "Windows":
                os.startfile(ruta)
            elif sistema == "Darwin":  # macOS
                subprocess.run(['open', str(ruta)])
            else:  # Linux
                subprocess.run(['xdg-open', str(ruta)])
        except:
            print(f"📁 Carpeta: {ruta.absolute()}")
    
    def obtener_info_video(self, url):
        """Obtiene información del video"""
        try:
            print("🔍 Conectando con YouTube...")
            yt = YouTube(url)
            
            print(f"\n📺 VIDEO ENCONTRADO:")
            print(f"   🎬 Título: {yt.title}")
            print(f"   👤 Canal: {yt.author}")
            print(f"   ⏱️  Duración: {self.formatear_duracion(yt.length)}")
            print(f"   👁️  Vistas: {yt.views:,}")
            
            return yt
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def formatear_duracion(self, segundos):
        """Formatea segundos a formato MM:SS o HH:MM:SS"""
        if segundos < 3600:
            return f"{segundos//60}:{segundos%60:02d}"
        else:
            return f"{segundos//3600}:{(segundos%3600)//60:02d}:{segundos%60:02d}"
    
    def descargar_mp3(self, url):
        """Descarga y convierte a MP3 con diálogo de guardar"""
        try:
            print("\n🎵 DESCARGANDO COMO MP3")
            print("═" * 60)
            
            yt = self.obtener_info_video(url)
            if not yt:
                return False
            
            # Preguntar dónde guardar
            nombre_base = self.limpiar_nombre(yt.title)
            extension = ".mp3"
            
            print(f"\n💾 ARCHIVO A GUARDAR: {nombre_base}{extension}")
            
            ubicacion, nombre_final = self.abrir_explorador_archivos(nombre_base, extension)
            
            if isinstance(ubicacion, tuple):  # Si abrir_explorador_archivos retornó tupla
                ubicacion, nombre_final = ubicacion
                ruta_completa = ubicacion / nombre_final
            else:
                ruta_completa = ubicacion / nombre_final
            
            # Verificar si el archivo ya existe
            if ruta_completa.exists():
                sobrescribir = input(f"⚠️  El archivo ya existe. ¿Sobrescribir? (s/n): ").lower()
                if sobrescribir != 's':
                    print("❌ Descarga cancelada")
                    return False
            
            # Descargar thumbnail
            print("\n📸 Obteniendo miniatura...")
            thumbnail_data = None
            thumbnail_candidates = [
                f"https://i.ytimg.com/vi/{yt.video_id}/maxresdefault.jpg",
                f"https://i.ytimg.com/vi/{yt.video_id}/sddefault.jpg",
                f"https://i.ytimg.com/vi/{yt.video_id}/hqdefault.jpg",
                yt.thumbnail_url
            ]
            
            for thumb_url in thumbnail_candidates:
                try:
                    response = requests.get(thumb_url, timeout=5)
                    if response.status_code == 200:
                        thumbnail_data = response.content
                        print("   ✅ Miniatura obtenida")
                        break
                except:
                    continue
            
            # Descargar audio
            print("🔊 Descargando audio...")
            audio_stream = yt.streams.get_audio_only()
            
            temp_audio = self.temp_dir / f"{uuid.uuid4()}.webm"
            temp_mp3 = self.temp_dir / f"{uuid.uuid4()}.mp3"
            
            print("   ⬇️ Descargando...", end="", flush=True)
            audio_stream.download(output_path=str(self.temp_dir), filename=temp_audio.name)
            print(" ✅")
            
            # Convertir a MP3
            print("🔄 Convirtiendo a MP3...", end="", flush=True)
            subprocess.run([
                "ffmpeg", "-y", "-i", str(temp_audio),
                "-vn", "-ab", "192k", str(temp_mp3)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(" ✅")
            
            # Añadir metadatos
            print("🏷️ Añadiendo metadatos...", end="", flush=True)
            try:
                audio = MP3(str(temp_mp3), ID3=ID3)
                if audio.tags is None:
                    audio.add_tags()
                
                audio.tags.add(TIT2(encoding=3, text=yt.title))
                audio.tags.add(TPE1(encoding=3, text=yt.author))
                audio.tags.add(TALB(encoding=3, text="YouTube"))
                
                if thumbnail_data:
                    audio.tags.add(APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,
                        desc='Cover',
                        data=thumbnail_data
                    ))
                
                audio.save(v2_version=3)
                print(" ✅")
            except Exception as e:
                print(f" ⚠️ (sin metadatos: {e})")
            
            # Mover a ubicación seleccionada
            print(f"\n💾 Guardando en: {ruta_completa}")
            shutil.move(str(temp_mp3), str(ruta_completa))
            
            # Limpiar temporal
            self.limpiar_temporal()
            
            # Mostrar información final
            tamaño_mb = ruta_completa.stat().st_size / (1024 * 1024)
            
            print(f"\n{'='*60}")
            print("✅ ¡DESCARGA COMPLETADA!")
            print(f"{'='*60}")
            print(f"   📁 Archivo: {nombre_final}")
            print(f"   📏 Tamaño: {tamaño_mb:.2f} MB")
            print(f"   📍 Ubicación: {ubicacion.absolute()}")
            
            # Preguntar si abrir carpeta
            abrir = input("\n📂 ¿Abrir carpeta de destino? (s/n): ").lower()
            if abrir == 's':
                self.abrir_carpeta(ubicacion)
            
            # Preguntar si reproducir
            reproducir = input("🎵 ¿Reproducir archivo ahora? (s/n): ").lower()
            if reproducir == 's':
                self.reproducir_archivo(ruta_completa)
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False
    
    def descargar_mp4(self, url, calidad=3):
        """Descarga y convierte a MP4 con diálogo de guardar"""
        try:
            # Mapeo de calidades
            calidades = {
                1: ("144p", "Baja"),
                2: ("360p", "Estándar"),
                3: ("720p", "HD"),
                4: ("1080p", "Full HD"),
                5: ("max", "Máxima")
            }
            
            resolucion, descripcion = calidades.get(calidad, ("720p", "HD"))
            
            print(f"\n🎬 DESCARGANDO COMO MP4 ({resolucion} - {descripcion})")
            print("═" * 60)
            
            yt = self.obtener_info_video(url)
            if not yt:
                return False
            
            # Preguntar dónde guardar
            nombre_base = f"{self.limpiar_nombre(yt.title)}_{resolucion}"
            extension = ".mp4"
            
            print(f"\n💾 ARCHIVO A GUARDAR: {nombre_base}{extension}")
            
            ubicacion, nombre_final = self.abrir_explorador_archivos(nombre_base, extension)
            
            if isinstance(ubicacion, tuple):  # Si abrir_explorador_archivos retornó tupla
                ubicacion, nombre_final = ubicacion
                ruta_completa = ubicacion / nombre_final
            else:
                ruta_completa = ubicacion / nombre_final
            
            # Verificar si el archivo ya existe
            if ruta_completa.exists():
                sobrescribir = input(f"⚠️  El archivo ya existe. ¿Sobrescribir? (s/n): ").lower()
                if sobrescribir != 's':
                    print("❌ Descarga cancelada")
                    return False
            
            # Descargar audio
            print("🔊 Descargando audio...")
            audio_stream = yt.streams.get_by_itag(140)
            if not audio_stream:
                audio_stream = yt.streams.get_audio_only()
            
            temp_audio = self.temp_dir / f"audio_{uuid.uuid4()}.m4a"
            audio_stream.download(output_path=str(self.temp_dir), filename=temp_audio.name)
            print("   ✅ Audio descargado")
            
            # Descargar video
            print("🎥 Descargando video...")
            if calidad == 5:  # Máxima calidad
                video_stream = yt.streams.filter(
                    mime_type="video/mp4",
                    progressive=False
                ).order_by("resolution").desc().first()
            else:
                video_stream = yt.streams.filter(
                    mime_type="video/mp4",
                    res=f"{resolucion}",
                    progressive=False
                ).first()
                
                if not video_stream and calidad == 4:  # Si no hay 1080p, intentar 720p
                    video_stream = yt.streams.filter(
                        mime_type="video/mp4",
                        res="720p",
                        progressive=False
                    ).first()
                    if video_stream:
                        resolucion = "720p"
                        nombre_final = nombre_final.replace("1080p", "720p")
                        print("   ⚠️  1080p no disponible, usando 720p")
            
            if not video_stream:
                print("❌ No se encontró video en la calidad solicitada")
                return False
            
            temp_video = self.temp_dir / f"video_{uuid.uuid4()}.mp4"
            video_stream.download(output_path=str(self.temp_dir), filename=temp_video.name)
            print("   ✅ Video descargado")
            
            # Combinar audio y video
            print("🔄 Combinando audio y video...")
            temp_combinado = self.temp_dir / f"combinado_{uuid.uuid4()}.mp4"
            
            subprocess.run([
                "ffmpeg", "-y",
                "-i", str(temp_video),
                "-i", str(temp_audio),
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                str(temp_combinado)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Mover a ubicación seleccionada
            print(f"\n💾 Guardando en: {ruta_completa}")
            shutil.move(str(temp_combinado), str(ruta_completa))
            
            # Limpiar temporal
            self.limpiar_temporal()
            
            # Mostrar información final
            tamaño_mb = ruta_completa.stat().st_size / (1024 * 1024)
            
            print(f"\n{'='*60}")
            print("✅ ¡DESCARGA COMPLETADA!")
            print(f"{'='*60}")
            print(f"   📁 Archivo: {nombre_final}")
            print(f"   📏 Tamaño: {tamaño_mb:.2f} MB")
            print(f"   🎬 Resolución: {resolucion}")
            print(f"   📍 Ubicación: {ubicacion.absolute()}")
            
            # Preguntar si abrir carpeta
            abrir = input("\n📂 ¿Abrir carpeta de destino? (s/n): ").lower()
            if abrir == 's':
                self.abrir_carpeta(ubicacion)
            
            # Preguntar si reproducir
            reproducir = input("🎬 ¿Reproducir video ahora? (s/n): ").lower()
            if reproducir == 's':
                self.reproducir_archivo(ruta_completa)
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False
    
    def reproducir_archivo(self, ruta_archivo):
        """Reproduce el archivo con el reproductor predeterminado"""
        sistema = platform.system()
        
        try:
            if sistema == "Windows":
                os.startfile(ruta_archivo)
            elif sistema == "Darwin":  # macOS
                subprocess.run(['open', str(ruta_archivo)])
            else:  # Linux
                subprocess.run(['xdg-open', str(ruta_archivo)])
            print("   ▶️  Reproduciendo...")
        except:
            print("   ⚠️  No se pudo abrir el reproductor")
    
    def mostrar_streams(self, url):
        """Muestra todos los streams disponibles"""
        try:
            yt = self.obtener_info_video(url)
            if not yt:
                return
            
            print("\n📊 STREAMS DISPONIBLES:")
            print("═" * 80)
            print(f"{'ITag':<6} {'Tipo':<20} {'Resolución':<12} {'FPS':<6} {'Audio':<8} {'Tamaño':<10}")
            print("═" * 80)
            
            streams_ordenados = sorted(yt.streams, key=lambda x: (
                x.mime_type,
                x.resolution or "",
                x.fps or 0
            ), reverse=True)
            
            for stream in streams_ordenados:
                tamaño = ""
                if stream.filesize:
                    tamaño = f"{stream.filesize / (1024*1024):.1f}MB"
                
                print(f"{stream.itag:<6} {stream.mime_type:<20} "
                      f"{str(stream.resolution or ''):<12} {str(stream.fps or ''):<6} "
                      f"{'✅' if stream.includes_audio_track else '❌':<8} {tamaño:<10}")
            
            print("═" * 80)
            
            # Recomendaciones
            print("\n💡 RECOMENDACIONES:")
            print("   Para MP3: Usar streams de audio solo (m4a)")
            print("   Para MP4: Buscar video sin audio (progressive=False) + audio separado")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def limpiar_temporal(self):
        """Limpia la carpeta temporal"""
        if self.temp_dir.exists():
            for archivo in self.temp_dir.glob("*"):
                try:
                    if archivo.is_file():
                        archivo.unlink()
                except:
                    pass
    
    def limpiar_nombre(self, nombre):
        """Limpia el nombre para usar como archivo"""
        caracteres_invalidos = '<>:"/\\|?*'
        for c in caracteres_invalidos:
            nombre = nombre.replace(c, '')
        return nombre[:100]  # Limitar longitud


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="YouTube Downloader - Descarga videos con ventana 'Guardar como'",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  ytdl.py mp3 https://youtu.be/dQw4w9WgXcQ
  ytdl.py mp4 https://youtu.be/dQw4w9WgXcQ --calidad 3
  ytdl.py info https://youtu.be/dQw4w9WgXcQ
  ytdl.py streams https://youtu.be/dQw4w9WgXcQ

Calidades MP4:
  1 = 144p      (calidad baja)
  2 = 360p      (calidad estándar)
  3 = 720p      (HD recomendado)
  4 = 1080p     (Full HD)
  5 = máxima    (mejor calidad disponible)
        """
    )
    
    subparsers = parser.add_subparsers(dest="comando", help="Comando a ejecutar")
    
    # Comando MP3
    mp3_parser = subparsers.add_parser("mp3", help="Descargar como MP3")
    mp3_parser.add_argument("url", help="URL del video de YouTube")
    
    # Comando MP4
    mp4_parser = subparsers.add_parser("mp4", help="Descargar como MP4")
    mp4_parser.add_argument("url", help="URL del video de YouTube")
    mp4_parser.add_argument("--calidad", type=int, choices=range(1, 6), default=3,
                          help="Calidad del video (1-5)")
    
    # Comando INFO
    info_parser = subparsers.add_parser("info", help="Mostrar información del video")
    info_parser.add_argument("url", help="URL del video de YouTube")
    
    # Comando STREAMS
    streams_parser = subparsers.add_parser("streams", help="Mostrar streams disponibles")
    streams_parser.add_argument("url", help="URL del video de YouTube")
    
    args = parser.parse_args()
    
    if not args.comando:
        parser.print_help()
        sys.exit(1)
    
    # Crear instancia del descargador
    descargador = YouTubeDownloaderCLI()
    descargador.mostrar_banner()
    
    try:
        if args.comando == "mp3":
            if not args.url.startswith(("http://", "https://")):
                print("❌ URL inválida. Debe comenzar con http:// o https://")
                sys.exit(1)
            descargador.descargar_mp3(args.url)
            
        elif args.comando == "mp4":
            if not args.url.startswith(("http://", "https://")):
                print("❌ URL inválida. Debe comenzar con http:// o https://")
                sys.exit(1)
            descargador.descargar_mp4(args.url, args.calidad)
            
        elif args.comando == "info":
            if not args.url.startswith(("http://", "https://")):
                print("❌ URL inválida. Debe comenzar con http:// o https://")
                sys.exit(1)
            descargador.obtener_info_video(args.url)
            
        elif args.comando == "streams":
            if not args.url.startswith(("http://", "https://")):
                print("❌ URL inválida. Debe comenzar con http:// o https://")
                sys.exit(1)
            descargador.mostrar_streams(args.url)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Operación cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()