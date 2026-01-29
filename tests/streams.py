from pytubefix import YouTube
from typing import List, Dict
import re


def parse_resolution(res: str) -> int:
    if not res or "p" not in res:
        return 0
    try:
        return int(res.replace("p", ""))
    except:
        return 0


def parse_bitrate(abr: str) -> int:
    if not abr or "kbps" not in abr:
        return 0
    try:
        return int(abr.replace("kbps", ""))
    except:
        return 0


def estimate_filesize_mb(stream, duration: int):
    # Tamaño real si existe
    if getattr(stream, "filesize_mb", None):
        return round(stream.filesize_mb, 2), False

    # Audio → usar abr
    if stream.type == "audio" and stream.abr:
        kbps = int(stream.abr.replace("kbps", ""))
        size = (kbps * duration) / 8 / 1024
        return round(size, 2), True

    # Video → estimación por resolución
    bitrate_map = {
        "144p": 150,
        "240p": 300,
        "360p": 800,
        "480p": 1200,
        "720p": 2500,
        "1080p": 4500,
    }

    if stream.resolution and duration:
        kbps = bitrate_map.get(stream.resolution, 2000)
        size = (kbps * duration) / 8 / 1024
        return round(size, 2), True

    return None, True


def get_available_streams(url: str) -> List[Dict]:
    yt = YouTube(url)
    streams_info = []

    for stream in yt.streams:
        size_mb, estimated = estimate_filesize_mb(stream, yt.length)

        info = {
            "itag": stream.itag,
            "type": stream.type,  # audio / video
            "mime_type": stream.mime_type,
            "resolution": stream.resolution,
            "abr": stream.abr,
            "fps": getattr(stream, "fps", None),
            "is_progressive": stream.is_progressive,
            "has_audio": stream.includes_audio_track,
            "filesize_mb": size_mb,
            "filesize_estimated": estimated,
            "filesize_display": (
                f"{size_mb} MB (estimado)"
                if size_mb and estimated
                else f"{size_mb} MB"
                if size_mb
                else "Desconocido"
            ),
            "codecs": stream.codecs if hasattr(stream, "codecs") else None,
        }

        streams_info.append(info)

    # Ordenar: video primero, luego resolución, luego bitrate
    streams_info.sort(
        key=lambda x: (
            0 if x["type"] == "video" else 1,
            parse_resolution(x.get("resolution")),
            parse_bitrate(x.get("abr")),
        ),
        reverse=True,
    )

    return streams_info


# ===========================
# PRUEBA DIRECTA
# ===========================
if __name__ == "__main__":
    url = input("Pega la URL del video: ").strip()

    streams = get_available_streams(url)

    print("\nSTREAMS DISPONIBLES:\n")
    for s in streams:
        print(
            f"[{s['type'].upper()}] "
            f"itag={s['itag']} | "
            f"res={s['resolution']} | "
            f"abr={s['abr']} | "
            f"fps={s['fps']} | "
            f"progressive={s['is_progressive']} | "
            f"size={s['filesize_display']}"
        )
