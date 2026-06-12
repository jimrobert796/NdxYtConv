# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="ndxYtConv",
    version="1.2.1",
    author="jimrobert796",
    author_email="",
    description="Herramienta ligera para convertir YouTube a mp3/mp4",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jimrobert796/NdxYtConv.git",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.12",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Environment :: Web Environment",
    ],
    install_requires=[
        "python-multipart==0.0.21", 
        "requests==2.32.3", 
        "fastapi==0.127.0", 
        "fastapi-cli==0.0.20", 
        "fastapi-cloud-cli==0.7.0", 
        "ffmpeg-python==0.2.0", 
        "gunicorn==23.0.0", 
        "Jinja2==3.1.6", 
        "mutagen==1.47.0", 
        "pyinstaller==6.18.0", 
        "pyinstaller-hooks-contrib==2026.0", 
        "pytubefix==9.4.1", 
        "requests==2.32.3", 
        "uvicorn==0.40.0"
    ],
    entry_points={
    "console_scripts": [
        "ndxytconv = ytconver.cli.ndxYtConv:main",
        "ndxytconv-web = ytconver.web.main:main",
        
    ]
},
)

