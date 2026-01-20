# core/downloader.py - CÓDIGO COMPARTIDO
from pytubefix import YouTube
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
import requests
import subprocess
import uuid
import os
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple
import time


@dataclass
class VideoInfo:
    """Información del video"""
    title: str
    author: str
    video_id: str
    duration: int
    views: int
    thumbnail_url: str
    length_formatted: str


class YouTubeDownloaderCore:
    """Clase base con toda la lógica de descarga"""
    
    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
    
    def get_video_info(self, url: str) -> Optional[VideoInfo]:
        """Obtiene información del video"""
        try:
            yt = YouTube(url)
            
            # Obtener mejor thumbnail
            thumbnail_candidates = [
                f"https://i.ytimg.com/vi/{yt.video_id}/maxresdefault.jpg",
                f"https://i.ytimg.com/vi/{yt.video_id}/sddefault.jpg",
                f"https://i.ytimg.com/vi/{yt.video_id}/hqdefault.jpg",
            ]
            
            thumbnail_url = yt.thumbnail_url
            for thumb_url in thumbnail_candidates:
                try:
                    response = requests.get(thumb_url, timeout=3)
                    if response.status_code == 200:
                        thumbnail_url = thumb_url
                        break
                except:
                    continue
            
            # Formatear duración
            duration = yt.length
            if duration < 3600:
                length_formatted = f"{duration//60}:{duration%60:02d}"
            else:
                length_formatted = f"{duration//3600}:{(duration%3600)//60:02d}:{duration%60:02d}"
            
            return VideoInfo(
                title=yt.title,
                author=yt.author,
                video_id=yt.video_id,
                duration=duration,
                views=yt.views,
                thumbnail_url=thumbnail_url,
                length_formatted=length_formatted
            )
            
        except Exception as e:
            raise Exception(f"Error obteniendo info: {str(e)}")
    
    def download_mp3(self, url: str, output_path: Optional[Path] = None) -> Path:
        """Descarga y convierte a MP3"""
        try:
            # Obtener información
            video_info = self.get_video_info(url)
            yt = YouTube(url)
            
            # Descargar thumbnail
            thumbnail_data = None
            try:
                response = requests.get(video_info.thumbnail_url, timeout=5)
                if response.status_code == 200:
                    thumbnail_data = response.content
            except:
                pass
            
            # Descargar audio
            audio_stream = yt.streams.get_audio_only()
            
            temp_audio = self.temp_dir / f"{uuid.uuid4()}.webm"
            temp_mp3 = self.temp_dir / f"{uuid.uuid4()}.mp3"
            
            audio_stream.download(output_path=str(self.temp_dir), filename=temp_audio.name)
            
            # Convertir a MP3
            subprocess.run([
                "ffmpeg", "-y", "-i", str(temp_audio),
                "-vn", "-ab", "192k", str(temp_mp3)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Añadir metadatos
            try:
                audio = MP3(str(temp_mp3), ID3=ID3)
                if audio.tags is None:
                    audio.add_tags()
                
                audio.tags.add(TIT2(encoding=3, text=video_info.title))
                audio.tags.add(TPE1(encoding=3, text=video_info.author))
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
            except Exception as e:
                print(f"Advertencia metadatos: {e}")
            
            # Definir ruta de salida
            if output_path is None:
                output_path = Path.cwd() / f"{self.sanitize_filename(video_info.title)}.mp3"
            
            # Mover archivo
            shutil.move(str(temp_mp3), str(output_path))
            
            # Limpiar temporal
            temp_audio.unlink(missing_ok=True)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Error descargando MP3: {str(e)}")
    
    def download_mp4(self, url: str, quality: int = 3, output_path: Optional[Path] = None) -> Path:
        """Descarga y convierte a MP4"""
        try:
            # Obtener información
            video_info = self.get_video_info(url)
            yt = YouTube(url)
            
            # Mapear calidad
            quality_map = {
                1: "144p",
                2: "360p",
                3: "720p",
                4: "1080p",
                5: "max"
            }
            
            resolution = quality_map.get(quality, "720p")
            
            # Descargar audio
            audio_stream = yt.streams.get_by_itag(140) or yt.streams.get_audio_only()
            temp_audio = self.temp_dir / f"audio_{uuid.uuid4()}.m4a"
            audio_stream.download(output_path=str(self.temp_dir), filename=temp_audio.name)
            
            # Descargar video
            if quality == 5:
                video_stream = yt.streams.filter(
                    mime_type="video/mp4",
                    progressive=False
                ).order_by("resolution").desc().first()
            else:
                video_stream = yt.streams.filter(
                    mime_type="video/mp4",
                    res=f"{resolution}",
                    progressive=False
                ).first()
                
                if not video_stream and resolution == "1080p":
                    video_stream = yt.streams.filter(
                        mime_type="video/mp4",
                        res="720p",
                        progressive=False
                    ).first()
                    resolution = "720p"
            
            if not video_stream:
                raise Exception("No se encontró video en la calidad solicitada")
            
            temp_video = self.temp_dir / f"video_{uuid.uuid4()}.mp4"
            video_stream.download(output_path=str(self.temp_dir), filename=temp_video.name)
            
            # Combinar
            temp_combined = self.temp_dir / f"combined_{uuid.uuid4()}.mp4"
            
            subprocess.run([
                "ffmpeg", "-y",
                "-i", str(temp_video),
                "-i", str(temp_audio),
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                str(temp_combined)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Definir ruta de salida
            if output_path is None:
                output_path = Path.cwd() / f"{self.sanitize_filename(video_info.title)}_{resolution}.mp4"
            
            # Mover archivo
            shutil.move(str(temp_combined), str(output_path))
            
            # Limpiar temporal
            temp_audio.unlink(missing_ok=True)
            temp_video.unlink(missing_ok=True)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Error descargando MP4: {str(e)}")
    
    def get_available_streams(self, url: str) -> list:
        """Obtiene lista de streams disponibles"""
        try:
            yt = YouTube(url)
            streams = []
            
            for stream in yt.streams:
                streams.append({
                    'itag': stream.itag,
                    'mime_type': stream.mime_type,
                    'resolution': stream.resolution,
                    'abr': stream.abr,
                    'fps': stream.fps,
                    'filesize': stream.filesize,
                    'has_audio': stream.includes_audio_track,
                    'is_progressive': stream.is_progressive
                })
            
            return streams
            
        except Exception as e:
            raise Exception(f"Error obteniendo streams: {str(e)}")
    
    def sanitize_filename(self, filename: str) -> str:
        """Limpia el nombre de archivo"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        return filename[:100]
    
    def cleanup(self):
        """Limpia archivos temporales"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)