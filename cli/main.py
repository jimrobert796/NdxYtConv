#!/usr/bin/env python3
# cli/main.py - VERSIÓN TERMINAL CON GUARDAR COMO
import sys
import argparse
import subprocess
import webbrowser
from pathlib import Path
import platform
import tempfile
import os

# Agregar el directorio core al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.downloader import YouTubeDownloaderCore, VideoInfo


class SaveDialog:
    """Maneja los diálogos de guardar archivo según el sistema operativo"""
    
    @staticmethod
    def get_save_path(default_filename: str, file_extension: str = "") -> Path:
        """
        Abre diálogo 'Guardar como' y retorna la ruta seleccionada.
        Retorna None si el usuario cancela.
        """
        sistema = platform.system()
        
        # Asegurar que la extensión tenga punto
        if file_extension and not file_extension.startswith("."):
            file_extension = "." + file_extension
        
        filename = default_filename + file_extension
        
        if sistema == "Windows":
            return SaveDialog._windows_save_dialog(filename)
        elif sistema == "Darwin":  # macOS
            return SaveDialog._macos_save_dialog(filename)
        else:  # Linux
            return SaveDialog._linux_save_dialog(filename)
    
    @staticmethod
    def _windows_save_dialog(filename: str) -> Path:
        """Diálogo de guardar para Windows"""
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            # Ocultar ventana principal de tkinter
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=Path(filename).suffix,
                initialfile=filename,
                title="Guardar archivo como",
                filetypes=[
                    ("Archivos compatibles", f"*{Path(filename).suffix}"),
                    ("Todos los archivos", "*.*")
                ]
            )
            
            root.destroy()
            
            if file_path:
                return Path(file_path)
            return None
            
        except ImportError:
            print("⚠️  Tkinter no disponible. Usando ubicación por defecto.")
            return SaveDialog._fallback_save_path(filename)
    
    @staticmethod
    def _macos_save_dialog(filename: str) -> Path:
        """Diálogo de guardar para macOS usando AppleScript"""
        try:
            # Escapar comillas en el nombre
            safe_filename = filename.replace('"', '\\"')
            
            applescript = f'''
            set theFolder to choose file name with prompt "Guardar como {safe_filename}" default name "{safe_filename}"
            POSIX path of theFolder
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return Path(result.stdout.strip())
            return None
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("⚠️  AppleScript no disponible. Usando ubicación por defecto.")
            return SaveDialog._fallback_save_path(filename)
    
    @staticmethod
    def _linux_save_dialog(filename: str) -> Path:
        """Diálogo de guardar para Linux usando zenity o kdialog"""
        # Primero intentar con zenity (Gnome)
        try:
            result = subprocess.run(
                ['zenity', '--file-selection', '--save',
                 '--title', f'Guardar {filename}',
                 '--filename', filename],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return Path(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Si zenity falla, intentar con kdialog (KDE)
        try:
            file_filter = f"*.{Path(filename).suffix.lstrip('.')}" if Path(filename).suffix else "*"
            result = subprocess.run(
                ['kdialog', '--getsavefilename', filename, file_filter],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return Path(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Si ambos fallan, usar fallback
        print("⚠️  Zenity/KDialog no disponibles. Usando ubicación por defecto.")
        return SaveDialog._fallback_save_path(filename)
    
    @staticmethod
    def _fallback_save_path(filename: str) -> Path:
        """Ubicación por defecto cuando no hay diálogo disponible"""
        downloads_path = Path.home() / "Downloads"
        downloads_path.mkdir(exist_ok=True)
        
        # Generar nombre único si ya existe
        counter = 1
        base_name = Path(filename).stem
        extension = Path(filename).suffix
        
        while (downloads_path / filename).exists():
            filename = f"{base_name}_{counter}{extension}"
            counter += 1
        
        return downloads_path / filename
    
    @staticmethod
    def open_file_location(file_path: Path):
        """Abre la carpeta que contiene el archivo"""
        sistema = platform.system()
        
        try:
            if sistema == "Windows":
                os.startfile(file_path.parent)
            elif sistema == "Darwin":  # macOS
                subprocess.run(['open', str(file_path.parent)])
            else:  # Linux
                subprocess.run(['xdg-open', str(file_path.parent)])
        except Exception as e:
            print(f"⚠️  No se pudo abrir la carpeta: {e}")


class YouTubeDownloaderCLI:
    """Interfaz de línea de comandos con diálogo Guardar Como"""
    
    def __init__(self):
        self.core = YouTubeDownloaderCore()
        self.save_dialog = SaveDialog()
    
    def run(self):
        """Ejecuta la aplicación CLI"""
        parser = argparse.ArgumentParser(
            description="🎬 YouTube Downloader - Versión Terminal con Guardar Como",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
📋 EJEMPLOS DE USO:
  ytdl mp3 https://youtu.be/dQw4w9WgXcQ
  ytdl mp4 https://youtu.be/dQw4w9WgXcQ --calidad 4
  ytdl info https://youtu.be/dQw4w9WgXcQ
  ytdl streams https://youtu.be/dQw4w9WgXcQ

🎛️  CALIDADES MP4:
  1 = 144p      (calidad baja)
  2 = 360p      (estándar)
  3 = 720p      (HD - recomendado)
  4 = 1080p     (Full HD)
  5 = máxima    (mejor calidad disponible)

💡 CONSEJOS:
  • Usa --no-dialog para descargar directamente sin diálogo
  • Usa --open para abrir la carpeta después de descargar
  • Usa --play para reproducir el archivo automáticamente
            """
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
        
        # MP3
        mp3_parser = subparsers.add_parser("mp3", help="🎵 Descargar como MP3")
        mp3_parser.add_argument("url", help="URL del video de YouTube")
        mp3_parser.add_argument("--no-dialog", action="store_true", 
                              help="Descargar sin abrir diálogo 'Guardar como'")
        mp3_parser.add_argument("--output", "-o", help="Ruta específica para guardar")
        mp3_parser.add_argument("--open", action="store_true", 
                              help="Abrir carpeta después de descargar")
        mp3_parser.add_argument("--play", action="store_true", 
                              help="Reproducir archivo después de descargar")
        
        # MP4
        mp4_parser = subparsers.add_parser("mp4", help="🎬 Descargar como MP4")
        mp4_parser.add_argument("url", help="URL del video de YouTube")
        mp4_parser.add_argument("--calidad", "-q", type=int, choices=range(1, 6), 
                               default=3, help="Calidad del video (1-5)")
        mp4_parser.add_argument("--no-dialog", action="store_true", 
                              help="Descargar sin abrir diálogo 'Guardar como'")
        mp4_parser.add_argument("--output", "-o", help="Ruta específica para guardar")
        mp4_parser.add_argument("--open", action="store_true", 
                              help="Abrir carpeta después de descargar")
        mp4_parser.add_argument("--play", action="store_true", 
                              help="Reproducir archivo después de descargar")
        
        # Info
        info_parser = subparsers.add_parser("info", help="📺 Mostrar información del video")
        info_parser.add_argument("url", help="URL del video de YouTube")
        
        # Streams
        streams_parser = subparsers.add_parser("streams", help="📊 Mostrar streams disponibles")
        streams_parser.add_argument("url", help="URL del video de YouTube")
        
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        try:
            self.show_banner()
            
            if args.command == "mp3":
                self.download_mp3(
                    args.url, 
                    not args.no_dialog,
                    args.output,
                    args.open,
                    args.play
                )
            elif args.command == "mp4":
                self.download_mp4(
                    args.url,
                    args.calidad,
                    not args.no_dialog,
                    args.output,
                    args.open,
                    args.play
                )
            elif args.command == "info":
                self.show_info(args.url)
            elif args.command == "streams":
                self.show_streams(args.url)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Operación cancelada por el usuario")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            self.core.cleanup()
    
    def show_banner(self):
        """Muestra el banner de la aplicación"""
        banner = """
╔══════════════════════════════════════════════════════════╗
║      🎬 YOUTUBE DOWNLOADER - GUARDAR COMO INTERACTIVO    ║
║         Con diálogo nativo para seleccionar ubicación    ║
╚══════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def download_mp3(self, url: str, use_dialog: bool = True, 
                    output_path: str = None, open_folder: bool = False,
                    play_file: bool = False):
        """Descarga MP3 con diálogo opcional"""
        try:
            print("🎵 OBTENIENDO INFORMACIÓN DEL VIDEO...")
            info = self.core.get_video_info(url)
            
            print(f"\n📺 VIDEO: {info.title}")
            print(f"👤 CANAL: {info.author}")
            print(f"⏱️  DURACIÓN: {info.length_formatted}")
            
            # Determinar ruta de guardado
            if output_path:
                save_path = Path(output_path)
                print(f"\n📁 Guardando en ruta especificada: {save_path}")
            elif use_dialog:
                print(f"\n📂 Abriendo diálogo 'Guardar como'...")
                default_name = self.core.sanitize_filename(info.title)
                save_path = self.save_dialog.get_save_path(default_name, ".mp3")
                
                if not save_path:
                    print("❌ El usuario canceló la operación")
                    return
                
                print(f"📍 Ruta seleccionada: {save_path}")
            else:
                # Sin diálogo, usar ubicación por defecto
                downloads = Path.home() / "Downloads"
                downloads.mkdir(exist_ok=True)
                default_name = self.core.sanitize_filename(info.title) + ".mp3"
                save_path = downloads / default_name
                print(f"\n📁 Guardando en: {save_path}")
            
            # Verificar si el archivo ya existe
            if save_path.exists():
                print(f"\n⚠️  El archivo ya existe: {save_path.name}")
                overwrite = input("   ¿Deseas sobrescribirlo? (s/n): ").strip().lower()
                if overwrite != 's':
                    # Generar nuevo nombre
                    counter = 1
                    stem = save_path.stem
                    while save_path.exists():
                        save_path = save_path.parent / f"{stem}_{counter}{save_path.suffix}"
                        counter += 1
                    print(f"📝 Nuevo nombre: {save_path.name}")
            
            # Descargar
            print(f"\n⬇️  DESCARGANDO MP3...")
            print("   Esto puede tomar unos momentos...")
            
            result = self.core.download_mp3(url, save_path)
            
            # Mostrar resultados
            size_mb = result.stat().st_size / (1024 * 1024)
            
            print(f"\n{'='*60}")
            print("✅ ¡DESCARGA COMPLETADA!")
            print(f"{'='*60}")
            print(f"   📁 Archivo: {result.name}")
            print(f"   📏 Tamaño: {size_mb:.2f} MB")
            print(f"   📍 Ubicación: {result.parent}")
            print(f"{'='*60}")
            
            # Acciones post-descarga
            if open_folder:
                print("\n📂 Abriendo carpeta de destino...")
                self.save_dialog.open_file_location(result)
            
            if play_file:
                print("🎵 Reproduciendo archivo...")
                self.play_file(result)
            
            print(f"\n🎉 ¡Listo! Archivo guardado exitosamente.")
            
        except Exception as e:
            print(f"\n❌ Error durante la descarga: {e}")
            raise
    
    def download_mp4(self, url: str, quality: int = 3, use_dialog: bool = True,
                    output_path: str = None, open_folder: bool = False,
                    play_file: bool = False):
        """Descarga MP4 con diálogo opcional"""
        try:
            # Mapeo de calidades
            quality_names = {
                1: ("144p", "Calidad baja"),
                2: ("360p", "Calidad estándar"),
                3: ("720p", "HD"),
                4: ("1080p", "Full HD"),
                5: ("max", "Máxima calidad")
            }
            
            resolution, desc = quality_names.get(quality, ("720p", "HD"))
            
            print(f"🎬 OBTENIENDO INFORMACIÓN ({resolution} - {desc})...")
            info = self.core.get_video_info(url)
            
            print(f"\n📺 VIDEO: {info.title}")
            print(f"👤 CANAL: {info.author}")
            print(f"⏱️  DURACIÓN: {info.length_formatted}")
            print(f"🎯 CALIDAD: {resolution}")
            
            # Determinar ruta de guardado
            if output_path:
                save_path = Path(output_path)
                print(f"\n📁 Guardando en ruta especificada: {save_path}")
            elif use_dialog:
                print(f"\n📂 Abriendo diálogo 'Guardar como'...")
                default_name = f"{self.core.sanitize_filename(info.title)}_{resolution}"
                save_path = self.save_dialog.get_save_path(default_name, ".mp4")
                
                if not save_path:
                    print("❌ El usuario canceló la operación")
                    return
                
                print(f"📍 Ruta seleccionada: {save_path}")
            else:
                # Sin diálogo, usar ubicación por defecto
                downloads = Path.home() / "Downloads"
                downloads.mkdir(exist_ok=True)
                default_name = f"{self.core.sanitize_filename(info.title)}_{resolution}.mp4"
                save_path = downloads / default_name
                print(f"\n📁 Guardando en: {save_path}")
            
            # Verificar si el archivo ya existe
            if save_path.exists():
                print(f"\n⚠️  El archivo ya existe: {save_path.name}")
                overwrite = input("   ¿Deseas sobrescribirlo? (s/n): ").strip().lower()
                if overwrite != 's':
                    # Generar nuevo nombre
                    counter = 1
                    stem = save_path.stem
                    while save_path.exists():
                        save_path = save_path.parent / f"{stem}_{counter}{save_path.suffix}"
                        counter += 1
                    print(f"📝 Nuevo nombre: {save_path.name}")
            
            # Descargar
            print(f"\n⬇️  DESCARGANDO MP4...")
            print("   Esto puede tomar varios minutos dependiendo del tamaño...")
            
            result = self.core.download_mp4(url, quality, save_path)
            
            # Mostrar resultados
            size_mb = result.stat().st_size / (1024 * 1024)
            
            print(f"\n{'='*60}")
            print("✅ ¡DESCARGA COMPLETADA!")
            print(f"{'='*60}")
            print(f"   📁 Archivo: {result.name}")
            print(f"   📏 Tamaño: {size_mb:.2f} MB")
            print(f"   🎬 Resolución: {resolution}")
            print(f"   📍 Ubicación: {result.parent}")
            print(f"{'='*60}")
            
            # Acciones post-descarga
            if open_folder:
                print("\n📂 Abriendo carpeta de destino...")
                self.save_dialog.open_file_location(result)
            
            if play_file:
                print("🎬 Reproduciendo video...")
                self.play_file(result)
            
            print(f"\n🎉 ¡Listo! Video guardado exitosamente.")
            
        except Exception as e:
            print(f"\n❌ Error durante la descarga: {e}")
            raise
    
    def show_info(self, url: str):
        """Muestra información del video"""
        try:
            info = self.core.get_video_info(url)
            
            print(f"\n{'='*60}")
            print("📺 INFORMACIÓN COMPLETA DEL VIDEO")
            print(f"{'='*60}")
            print(f"   🎬 TÍTULO: {info.title}")
            print(f"   👤 CANAL: {info.author}")
            print(f"   🆔 ID: {info.video_id}")
            print(f"   ⏱️  DURACIÓN: {info.length_formatted} ({info.duration} segundos)")
            print(f"   👁️  VISTAS: {info.views:,}")
            print(f"   🖼️  THUMBNAIL: {info.thumbnail_url}")
            print(f"{'='*60}")
            
            # Opción para abrir thumbnail en navegador
            open_thumb = input("\n¿Abrir thumbnail en navegador? (s/n): ").strip().lower()
            if open_thumb == 's':
                webbrowser.open(info.thumbnail_url)
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_streams(self, url: str):
        """Muestra streams disponibles"""
        try:
            streams = self.core.get_available_streams(url)
            
            print(f"\n{'='*80}")
            print("📊 STREAMS DISPONIBLES")
            print(f"{'='*80}")
            print(f"{'ITag':<6} {'Tipo':<20} {'Resolución':<12} {'FPS':<6} "
                  f"{'Audio':<8} {'Tamaño':<10} {'Progresivo':<12}")
            print(f"{'='*80}")
            
            # Filtrar y ordenar streams
            video_streams = [s for s in streams if s['mime_type'].startswith('video')]
            audio_streams = [s for s in streams if s['mime_type'].startswith('audio')]
            
            # Mostrar streams de video
            print("\n🎬 STREAMS DE VIDEO:")
            for stream in sorted(video_streams, key=lambda x: (
                x['resolution'] or '',
                x['fps'] or 0
            ), reverse=True):
                self._print_stream_info(stream)
            
            # Mostrar streams de audio
            print("\n🎵 STREAMS DE AUDIO:")
            for stream in sorted(audio_streams, key=lambda x: x['abr'] or '', reverse=True):
                self._print_stream_info(stream)
            
            print(f"{'='*80}")
            print(f"Total: {len(streams)} streams disponibles")
            
            # Recomendaciones
            print(f"\n💡 RECOMENDACIONES:")
            print("   • Para MP3: Busca streams con 'mime_type' que contenga 'audio'")
            print("   • Para MP4: Busca video sin audio (progressive=False) + audio separado")
            print("   • Mejor calidad de audio: itag 140 (m4a, 128kbps)")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def _print_stream_info(self, stream):
        """Imprime información de un stream"""
        size = f"{stream['filesize']/(1024*1024):.1f}MB" if stream['filesize'] else "N/A"
        audio = "✅" if stream['has_audio'] else "❌"
        progressive = "✅" if stream['is_progressive'] else "❌"
        
        print(f"{stream['itag']:<6} {stream['mime_type']:<20} "
              f"{stream['resolution'] or '':<12} {stream['fps'] or '':<6} "
              f"{audio:<8} {size:<10} {progressive:<12}")
    
    def play_file(self, file_path: Path):
        """Reproduce un archivo con el reproductor predeterminado"""
        sistema = platform.system()
        
        try:
            if sistema == "Windows":
                os.startfile(file_path)
            elif sistema == "Darwin":  # macOS
                subprocess.run(['open', str(file_path)])
            else:  # Linux
                subprocess.run(['xdg-open', str(file_path)])
            print("   ▶️  Reproduciendo...")
        except Exception as e:
            print(f"   ⚠️  No se pudo abrir el reproductor: {e}")


def main():
    """Punto de entrada CLI"""
    app = YouTubeDownloaderCLI()
    app.run()


if __name__ == "__main__":
    main()