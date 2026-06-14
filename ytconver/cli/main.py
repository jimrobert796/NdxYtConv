#!/usr/bin/env python3
# cli/main.py - VERSIÓN TERMINAL
import sys
import argparse
import subprocess
import webbrowser
from pathlib import Path
import platform
import tempfile
import os
from rich import print  # ¡Reemplaza el print estándar!
from rich_argparse import RichHelpFormatter

#Colores predeterminados para gusto gracias a rich_argparse
RichHelpFormatter.styles["argparse.args"] = "Bold cyan"        # opciones --flag
RichHelpFormatter.styles["argparse.groups"] = "Bold yellow"    # títulos de sección
RichHelpFormatter.styles["argparse.help"] = "white"       # texto de ayuda
RichHelpFormatter.styles["argparse.metavar"] = "dim"      # <url>, <ruta>...

# Agregar el directorio core al path
sys.path.insert(0, str(Path(__file__).parent.parent))


from core.downloader import YouTubeDownloaderCore, VideoInfo

class YouTubeDownloaderCLI:
    """Interfaz de línea de comandos con diálogo Guardar Como"""

    def __init__(self):
        self.core = YouTubeDownloaderCore()

    def run(self):
        """Ejecuta la aplicación CLI"""
        parser = argparse.ArgumentParser(
            description="NdxYtConver - ver 1.3.1",
            formatter_class=RichHelpFormatter,
        )

        subparsers = parser.add_subparsers(
            dest="command", help="Comando a ejecutar")

        # MP3 parser para ejecucion
        mp3_parser = subparsers.add_parser("mp3", help="Descargar como MP3", formatter_class=RichHelpFormatter)
        
        mp3_parser.add_argument("url", help="URL del video de YouTube")
        mp3_parser.add_argument("--output", help="Ruta específica para guardar")

        # MP4
        mp4_parser = subparsers.add_parser("mp4", help="Descargar como MP4",  formatter_class=RichHelpFormatter)
        
        mp4_parser.add_argument("url", help="URL del video de YouTube")
        mp4_parser.add_argument("--calidad", "-q", type=int, choices=range(1, 8),default=5, help="Calidad del video (1-7)")
        mp4_parser.add_argument("--output", help="Ruta específica para guardar")

        # Info
        info_parser = subparsers.add_parser("info", help=" Mostrar información del video",  formatter_class=RichHelpFormatter)
        info_parser.add_argument("url", help="URL del video de YouTube")

        # Streams
        streams_parser = subparsers.add_parser("streams", help=" Mostrar streams disponibles",  formatter_class=RichHelpFormatter)
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
                    args.output
                )
            elif args.command == "mp4":
                self.download_mp4(
                    args.url,
                    args.calidad,
                    args.output
                )
            elif args.command == "info":
                self.show_info(args.url)
            elif args.command == "streams":
                self.show_streams(args.url)

        except KeyboardInterrupt:
            print("\n\nOperación cancelada por el usuario")
        except Exception as e:
            print(f"\nError: {e}")
        finally:
            self.core.cleanup()

    def show_banner(self):
        """Muestra el banner de la aplicación"""
        banner = """
NdxYtConver - ver 1.3.1"""
        print(banner)

    def download_mp3(self, url: str, use_dialog: bool = True,
                    output_path: str = None):
        """Descarga MP3 con diálogo opcional"""
        try:
            info = self.core.get_video_info(url)

            print(f"\n[bold cyan]Titulo:[/bold cyan] {info.title}")
            print(f"[bold green]Canal:[/bold green] {info.author}")
            print(f"[bold yellow]Duracion:[/bold yellow] {info.length_formatted}")

            # Determinar ruta de guardado
            if output_path:
                #save_path = Path(output_path)
                print(f"\n[bold green]Ruta de destino especificada: [/bold green]{save_path}")
            else:
                # En caso no se proporcione una ruta usara la default de donde este el usuario
                userDir = Path.cwd() # Ubicacion donde se encuentra el usuario
                userDir.mkdir(exist_ok=True)
                default_name = self.core.sanitize_filename(info.title) + ".mp3"
                save_path = userDir / default_name
                print(f"\n[bold green]Ruta de destino: [/bold green]{save_path}")

            # Verificar si el archivo ya existe
            if save_path.exists():
                print(f"\n[bold yellow]El archivo ya existe: [/bold yellow]{save_path.name}")
                overwrite = input(
                    "¿Deseas sobrescribirlo? (s/n): ").strip().lower()
                if overwrite != 's':
                    # Generar nuevo nombre
                    counter = 1
                    stem = save_path.stem
                    while save_path.exists():
                        save_path = save_path.parent / \
                            f"{stem}_{counter}{save_path.suffix}"
                        counter += 1
                    print(f"Nuevo nombre: {save_path.name}")

            # Descargar
            #print(f"\nDESCARGANDO MP3...")
            #print("   Esto puede tomar unos momentos...")

            result = self.core.download_mp3(url, save_path)

            # Mostrar resultados
            size_mb = result.stat().st_size / (1024 * 1024)


            print(f"[bold cyan]Archivo: [/bold cyan]{result.name}")
            print(f"[bold yellow]Tamaño: [/bold yellow]{size_mb:.2f} MB")
            print(f"[bold green]Ubicación: [/bold green]{result.parent}")

            print(f"\n[bold green]Archivo guardado exitosamente[/bold green]")

        except Exception as e:
            print(f"\n[bold red]Error durante la descarga: [/bold red]{e}")
            raise

    def download_mp4(self, url: str, quality: int = 5, use_dialog: bool = True,
                    output_path: str = None):
        """Descarga MP4 con diálogo opcional"""
        try:
            # Mapeo de calidades
            # Mapeo de calidades ACTUALIZADO
            quality_names = {
                1: ("144p", "Calidad baja"),
                2: ("240p", "Media-baja"),     #  NUEVO
                3: ("360p", "Estándar"),
                4: ("480p", "DVD calidad"),    #  NUEVO
                5: ("720p", "HD"),
                6: ("1080p", "Full HD"),
                7: ("max", "Máxima calidad")
                }

            resolution, desc = quality_names.get(quality, ("720p", "HD"))

            print(f"\nSelecionado: ({resolution} - {desc})")
            info = self.core.get_video_info(url)

            print(f"\n[bold cyan]Titulo:[/bold cyan] {info.title}")
            print(f"[bold green]Canal: [/bold green]{info.author}")
            print(f"[bold magenta]Duracion: [/bold magenta]{info.length_formatted}")
            print(f"[bold yellow]Calidad: [/bold yellow]{resolution}")

            # Determinar ruta de guardado
            if output_path:
                save_path = Path(output_path)
                print(f"\n[bold greenRuta de destino especificada: [/bold green{save_path}")
            else:
                # En caso no se proporcione una ruta usara la default de donde este el usuario
                userDir = Path.cwd() # Ubicacion donde se encuentra el usuario
                userDir.mkdir(exist_ok=True)
                default_name = self.core.sanitize_filename(info.title) + ".mp4"
                save_path = userDir / default_name
                print(f"\n[bold green]Ruta de destino: [/bold green]{save_path}")

            # Verificar si el archivo ya existe
            if save_path.exists():
                print(f"\n[bold yellow]El archivo ya existe: [/bold yellow]{save_path.name}")
                overwrite = input(
                    "   ¿Deseas sobrescribirlo? (s/n): ").strip().lower()
                if overwrite != 's':
                    # Generar nuevo nombre
                    counter = 1
                    stem = save_path.stem
                    while save_path.exists():
                        save_path = save_path.parent / \
                            f"{stem}_{counter}{save_path.suffix}"
                        counter += 1
                    print(f"Nuevo nombre: {save_path.name}")

            result = self.core.download_mp4(url, quality, save_path)

            # Mostrar resultados
            size_mb = result.stat().st_size / (1024 * 1024)

      
            print(f"[bold cyan]Archivo: [bold cyan]{result.name}")
            print(f"[bold yellow]Tamaño: [/bold yellow]{size_mb:.2f} MB")
            print(f"[bold magenta]Resolucion: [bold magenta]{resolution}")
            print(f"[bold green]Ubicacion: [/bold green]{result.parent}")
          
            print(f"\n[bold green]Video guardado exitosamente[/bold green]")

        except Exception as e:
            print(f"\n[bold red]Error durante la descarga: [/red green]{e}")
            raise

    def show_info(self, url: str):
        """Muestra información del video"""
        try:
            info = self.core.get_video_info(url)

            print(f"\n{'='*60}")
            print("INFORMACIÓN COMPLETA DEL VIDEO")
            print(f"{'='*60}")
            print(f"    TÍTULO: {info.title}")
            print(f"    CANAL: {info.author}")
            print(f"    ID: {info.video_id}")
            print(
                f"     DURACIÓN: {info.length_formatted} ({info.duration} segundos)")
            print(f"     VISTAS: {info.views:,}")
            print(f"     THUMBNAIL: {info.thumbnail_url}")
            print(f"{'='*60}")

            # Opción para abrir thumbnail en navegador
            open_thumb = input(
                "\n¿Abrir thumbnail en navegador? (s/n): ").strip().lower()
            if open_thumb == 's':
                webbrowser.open(info.thumbnail_url)

        except Exception as e:
            print(f" Error: {e}")

    def show_streams(self, url: str):
        """Muestra streams disponibles"""
        try:
            streams = self.core.get_available_streams(url)

            print(f"\n{'='*80}")
            print(" STREAMS DISPONIBLES")
            print(f"{'='*80}")
            print(f"{'ITag':<6} {'Tipo':<20} {'Resolución':<12} {'FPS':<6} "
                    f"{'Audio':<8} {'Tamaño':<10} {'Progresivo':<12}")
            print(f"{'='*80}")

            # Filtrar y ordenar streams
            video_streams = [s for s in streams if s['type'] == 'video']
            audio_streams = [s for s in streams if s['type'] == 'audio']

            # Mostrar streams de video
            print("\n STREAMS DE VIDEO:")
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
            print(f"\n RECOMENDACIONES:")
            print("   • Para MP3: Busca streams con 'mime_type' que contenga 'audio'")
            print(
                "   • Para MP4: Busca video sin audio (progressive=False) + audio separado")
            print("   • Mejor calidad de audio: itag 140 (m4a, 128kbps)")

        except Exception as e:
            print(f" Error: {e}")
            
    # Se ha refactorizado la funcion para arreglar errores en pantalla
    def _print_stream_info(self, stream):
        """Imprime información completa y segura de un stream"""

        size = (
            f"{stream['filesize']:.1f}MB"
            if stream.get('filesize')
            else "N/A"
        )

        fps = stream['fps'] if stream.get('fps') else "-"
        res = stream['resolution'] if stream.get('resolution') else "-"
        abr = stream['abr'] if stream.get('abr') else "-"
        audio = "Yes" if stream.get('has_audio') else "No"
        progressive = "Yes" if stream.get('is_progressive') else "No"

        print(
            f"{stream['itag']:<6} "
            f"{stream['type']:<6} "
            f"{res:<10} "
            f"{fps:<4} "
            f"{abr:<8} "
            f"{audio:<6} "
            f"{size:<10} "
            f"{progressive:<6} "
            f"{stream['mime_type']}"
        )
"""
    def play_file(self, file_path: Path):
        Reproduce un archivo con el reproductor predeterminado
        sistema = platform.system()

        try:
            if sistema == "Windows":
                os.startfile(file_path)
            elif sistema == "Darwin":  # macOS
                subprocess.run(['open', str(file_path)])
            else:  # Linux
                subprocess.run(['xdg-open', str(file_path)])
            print("     Reproduciendo...")
        except Exception as e:
            print(f"     No se pudo abrir el reproductor: {e}")
"""

def main():
    """Punto de entrada CLI"""
    app = YouTubeDownloaderCLI()
    app.run()


if __name__ == "__main__":
    main()
