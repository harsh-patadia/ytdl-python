from fastapi import FastAPI, Query, HTTPException
from pytube import YouTube
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
import os
from urllib.parse import urlparse, parse_qs

app = FastAPI()


def extract_video_id(url: str) -> str:
    """
    Extract video ID from YouTube URL (works for shorts, youtu.be, watch, etc.)
    """
    parsed_url = urlparse(url)

    # Handle youtu.be short links
    if 'youtu.be' in parsed_url.netloc:
        return parsed_url.path.lstrip('/')

    # Handle shorts
    if 'shorts' in parsed_url.path:
        return parsed_url.path.split('/shorts/')[-1].split('?')[0]

    # Handle standard /watch?v=ID
    if parsed_url.path == '/watch':
        qs = parse_qs(parsed_url.query)
        return qs.get('v', [None])[0]

    # fallback: maybe already cleaned?
    return None


@app.get("/")
def root():
    return {"message": "YouTube Downloader API is running. Use /download?url=..."}


@app.get("/download")
def download_video(url: str = Query(..., description="YouTube video URL")):
    try:
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid or unsupported YouTube URL format.")

        clean_url = f"https://www.youtube.com/watch?v={video_id}"
        yt = YouTube(clean_url)
        stream = yt.streams.get_highest_resolution()

        output_dir = "downloads"
        os.makedirs(output_dir, exist_ok=True)
        file_path = stream.download(output_path=output_dir)
        filename = yt.title.replace(" ", "_") + ".mp4"

        return FileResponse(
            file_path,
            media_type="video/mp4",
            filename=filename,
            background=BackgroundTask(lambda: os.remove(file_path))  # auto-cleanup
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")
