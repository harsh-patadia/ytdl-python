from fastapi import FastAPI, Query, HTTPException
from pytube import YouTube
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
import os
from urllib.parse import urlparse, parse_qs
import logging

app = FastAPI()

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("yt-downloader")


def extract_video_id(url: str) -> str:
    logger.info(f"Raw URL received: {url}")

    parsed_url = urlparse(url)
    logger.info(f"Parsed URL: {parsed_url}")

    # Check for obvious mistakes
    if not parsed_url.scheme.startswith("http"):
        logger.warning("URL scheme is not valid (missing http/https?)")
        return None

    # Handle youtu.be short links
    if 'youtu.be' in parsed_url.netloc:
        video_id = parsed_url.path.lstrip('/')
        logger.info(f"Detected youtu.be link. Video ID: {video_id}")
        return video_id

    # Handle shorts
    if 'shorts' in parsed_url.path:
        video_id = parsed_url.path.split('/shorts/')[-1].split('?')[0]
        logger.info(f"Detected Shorts link. Video ID: {video_id}")
        return video_id

    # Handle watch?v=ID
    if parsed_url.path == '/watch':
        query = parse_qs(parsed_url.query)
        video_id = query.get('v', [None])[0]
        logger.info(f"Detected watch link. Video ID: {video_id}")
        return video_id

    logger.warning("URL format not recognized")
    return None


@app.get("/")
def root():
    return {"message": "YouTube Downloader API is running. Use /download?url=..."}


@app.get("/download")
def download_video(url: str = Query(..., description="YouTube video URL")):
    try:
        logger.info(f"Received request to download: {url}")
        video_id = extract_video_id(url)

        if not video_id:
            raise ValueError("Invalid or unsupported YouTube URL format.")

        clean_url = f"https://www.youtube.com/watch?v={video_id}"
        logger.info(f"Cleaned YouTube URL: {clean_url}")

        yt = YouTube(clean_url)
        logger.info(f"Video Title: {yt.title}")
        stream = yt.streams.get_highest_resolution()
        logger.info(f"Selected stream: {stream.mime_type}, {stream.resolution}")

        output_dir = "downloads"
        os.makedirs(output_dir, exist_ok=True)

        file_path = stream.download(output_path=output_dir)
        logger.info(f"Downloaded to: {file_path}")

        filename = yt.title.replace(" ", "_") + ".mp4"

        return FileResponse(
            file_path,
            media_type="video/mp4",
            filename=filename,
            background=BackgroundTask(lambda: os.remove(file_path))
        )

    except Exception as e:
        logger.error(f"Error while downloading: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")
