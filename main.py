from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from pytube import YouTube
import os
from urllib.parse import urlparse, parse_qs
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("yt-downloader")

def clean_youtube_url(url: str) -> str:
    logger.info(f"Raw URL input: {url}")

    # Remove accidental 'l' prefix (common typo)
    if url.startswith("lhttp"):
        url = url[1:]

    parsed = urlparse(url)

    if parsed.scheme not in ['http', 'https']:
        logger.warning("Invalid URL scheme.")
        return None

    netloc = parsed.netloc.lower()
    path = parsed.path

    # Handle youtu.be short links
    if 'youtu.be' in netloc:
        video_id = path.lstrip('/')
        return f"https://www.youtube.com/watch?v={video_id}"

    # Handle shorts
    if 'shorts' in path:
        try:
            video_id = path.split('/shorts/')[-1].split('?')[0]
            return f"https://www.youtube.com/watch?v={video_id}"
        except IndexError:
            logger.error("Could not extract video ID from shorts URL.")
            return None

    # Handle watch URL
    if path == '/watch':
        query = parse_qs(parsed.query)
        video_id = query.get('v', [None])[0]
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"

    logger.warning("Unsupported or malformed URL.")
    return None


@app.get("/")
def root():
    return {"message": "YouTube Downloader API is running. Use /download?url=..."}


@app.get("/download")
def download_video(url: str = Query(..., description="YouTube video URL")):
    try:
        cleaned_url = clean_youtube_url(url)
        if not cleaned_url:
            raise HTTPException(status_code=400, detail="Invalid or unsupported YouTube URL.")

        logger.info(f"Cleaned URL: {cleaned_url}")

        yt = YouTube(cleaned_url)
        stream = yt.streams.get_highest_resolution()

        output_dir = "downloads"
        os.makedirs(output_dir, exist_ok=True)
        file_path = stream.download(output_path=output_dir)
        filename = yt.title.replace(" ", "_") + ".mp4"

        logger.info(f"Video downloaded: {filename}")

        return FileResponse(
            file_path,
            media_type="video/mp4",
            filename=filename,
            background=BackgroundTask(lambda: os.remove(file_path))
        )

    except Exception as e:
        logger.error(f"Download failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")
