#!/usr/bin/env python3
# - VERSIÓN MÁS ROBUSTA
import sys
import os
import argparse
from pathlib import Path

# Agregar el directorio core al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.main import YouTubeDownloaderCLI

class InteractiveCLI:
    def __init__(self):
        self.app = YouTubeDownloaderCLI()
        self.parser = self.create_custom_parser()

    def create_custom_parser(self):
        """Crea un parser personalizado que no hace sys.exit() en --help"""
        parser = argparse.ArgumentParser(
            description="🎬 NdxYtConv - Win-Ver 1.4",
            add_help=False,  # IMPORTANTE: Desactivar --help automático
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        subparsers = parser.add_subparsers(dest="command", help="Comandos")

        # MP3
        mp3_parser = subparsers.add_parser(
            "mp3", help="🎵 Descargar como MP3", add_help=False)
        mp3_parser.add_argument("url", help="URL de YouTube")
        mp3_parser.add_argument(
            "--no-dialog", action="store_true", help="Sin diálogo de guardar")
        mp3_parser.add_argument("--output", "-o", help="Ruta de salida")

        # MP4
        mp4_parser = subparsers.add_parser(
            "mp4", help="🎬 Descargar como MP4", add_help=False)
        mp4_parser.add_argument("url", help="URL de YouTube")
        mp4_parser.add_argument(
            "--calidad", "-q", type=int, choices=range(1, 8), default=5)  # ✅ 1-7, default 5
        mp4_parser.add_argument(
            "--no-dialog", action="store_true", help="Sin diálogo de guardar")
        mp4_parser.add_argument("--output", "-o", help="Ruta de salida")

        # Info
        info_parser = subparsers.add_parser(
            "info", help="📺 Mostrar información", add_help=False)
        info_parser.add_argument("url", help="URL de YouTube")

        # Streams
        streams_parser = subparsers.add_parser(
            "streams", help="📊 Mostrar streams", add_help=False)
        streams_parser.add_argument("url", help="URL de YouTube")

        return parser

    def show_help(self, command=None):
        """Muestra ayuda personalizada"""
        if command:
            print(f"\n📖 Ayuda para '{command}':")

            if command == "mp3":
                print("""
  mp3 <URL> [opciones]
  
  OPCIONES:
    --no-dialog    Descargar sin abrir diálogo 'Guardar como'
    -o, --output   Ruta específica para guardar el archivo
    
  EJEMPLOS:
    mp3 https://youtu.be/ejemplo
    mp3 https://youtu.be/ejemplo --no-dialog
    mp3 https://youtu.be/ejemplo -o "C:\\Musica\\cancion.mp3"
                """)
            elif command == "mp4":
                print("""
  mp4 <URL> [opciones]
  
  OPCIONES:
    -q, --calidad <1-7>  Calidad del video (1=baja, 7=alta)
    --no-dialog          Descargar sin abrir diálogo 'Guardar como'
    -o, --output         Ruta específica para guardar el archivo
    
  CALIDADES:
    1 = 144p  (baja calidad)
    2 = 240p  (media-baja)    
    3 = 360p  (estándar)
    4 = 480p  (DVD calidad)   
    5 = 720p  (HD - RECOMENDADO)
    6 = 1080p (Full HD)
    7 = máxima calidad
    
  EJEMPLOS:
    mp4 https://youtu.be/ejemplo              # Descarga 720p (default)
    mp4 https://youtu.be/ejemplo -q 4         # Descarga 480p
    mp4 https://youtu.be/ejemplo --no-dialog  # Descarga sin ventana (Si ya tienes ruta)
                """)
            elif command == "info":
                print("""
  info <URL>
  
  Muestra información detallada del video.
  
  EJEMPLO:
    info https://youtu.be/ejemplo
                """)
            elif command == "streams":
                print("""
  streams <URL>
  
  Muestra todos los streams disponibles del video.
  
  EJEMPLO:
    streams https://youtu.be/ejemplo
                """)
        else:
            # Ayuda general
            print("""
🎬 NdxYtConv - Comandos disponibles:

  mp3 <URL>      - Descargar audio como MP3
  mp4 <URL>      - Descargar video como MP4
  info <URL>     - Mostrar información del video
  streams <URL>  - Mostrar streams disponibles

💡 Para ayuda específica:
  help mp3      - Ayuda sobre descarga MP3
  help mp4      - Ayuda sobre descarga MP4
  help info     - Ayuda sobre información
  help streams  - Ayuda sobre streams

🔄 COMANDOS INTERACTIVOS:
  clear, cls    - Limpiar pantalla
  salir, exit   - Salir del programa
  Ctrl+C       - Salir inmediatamente
            """)

    def execute_command(self, args):
        """Ejecuta un comando parseado"""
        try:
            parsed_args = self.parser.parse_args(args)

            if not parsed_args.command:
                self.show_help()
                return

            # Mostrar banner
            self.app.show_banner()

            # Ejecutar comando
            if parsed_args.command == "mp3":
                self.app.download_mp3(
                    parsed_args.url,
                    not parsed_args.no_dialog,
                    parsed_args.output
                )
            elif parsed_args.command == "mp4":
                self.app.download_mp4(
                    parsed_args.url,
                    parsed_args.calidad,
                    not parsed_args.no_dialog,
                    parsed_args.output
                )
            elif parsed_args.command == "info":
                self.app.show_info(parsed_args.url)
            elif parsed_args.command == "streams":
                self.app.show_streams(parsed_args.url)

        except SystemExit:
            # No hacer nada, solo continuar
            pass
        except Exception as e:
            print(f"❌ Error: {e}")

    def run_interactive(self):
        """Ejecuta modo interactivo"""
        print("""
🎬 NdxYtConv - Win-Ver 1.4
Escribe '--help' para ayuda | Ctrl+C para salir
""")

        while True:
            try:
                print("─" * 50)
                cmd = input("NdxYtConv> ").strip()

                if not cmd:
                    continue

                parts = cmd.split()
                first = parts[0].lower()

                # Comandos especiales
                if first in ['salir', 'exit', 'quit']:
                    print("👋 ¡Hasta luego!")
                    break

                if first == 'help':
                    if len(parts) > 1:
                        self.show_help(parts[1])
                    else:
                        self.show_help()
                    continue

                if first in ['clear', 'cls']:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("""
🎬 NdxYtConv - Win-Ver 1.4
Escribe '--help' para ayuda | Ctrl+C para salir
""")
                    continue

                # Verificar si es --help
                if '--help' in parts or '-h' in parts:
                    # Extraer comando principal si existe
                    command = None
                    for part in parts:
                        if part in ['mp3', 'mp4', 'info', 'streams']:
                            command = part
                            break
                    self.show_help(command)
                    continue

                # Ejecutar comando normal
                self.execute_command(parts)

            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    """Punto de entrada"""
    cli = InteractiveCLI()

    # Si hay argumentos, modo comando único
    if len(sys.argv) > 1:
        # Verificar si es --help
        if '--help' in sys.argv or '-h' in sys.argv:
            cli.show_help()
            # Esperar si es ejecutable
            if getattr(sys, 'frozen', False):
                print("\nPresiona Enter para salir...")
                try:
                    input()
                except:
                    pass
            return

        # Ejecutar comando
        cli.execute_command(sys.argv[1:])

        # Esperar si es ejecutable
        if getattr(sys, 'frozen', False):
            print("\nPresiona Enter para salir...")
            try:
                input()
            except:
                pass
    else:
        # Modo interactivo
        cli.run_interactive()


if __name__ == "__main__":
    main()   