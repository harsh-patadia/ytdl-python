from fastapi import FastAPI, Query, HTTPException
from pytube import YouTube
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
import os
from urllib.parse import urlparse, parse_qs, urlunparse

app = FastAPI()

def sanitize_youtube_url(url: str) -> str:
    """Clean and convert YouTube Shorts URLs to regular watch URLs."""
    try:
        parsed = urlparse(url)

        if 'shorts' in parsed.path:
            # Convert /shorts/VIDEO_ID to /watch?v=VIDEO_ID
            video_id = parsed.path.split('/shorts/')[-1]
            return f"https://www.youtube.com/watch?v={video_id}"

        # If it's already a watch link, strip unnecessary params
        if parsed.path == '/watch':
            query = parse_qs(parsed.query)
            video_id = query.get('v', [None])[0]
            if video_id:
                return f"https://www.youtube.com/watch?v={video_id}"

        return url  # fallback
    except Exception:
        return url

@app.get("/download")
def download_video(url: str = Query(..., description="YouTube video URL")):
    try:
        cleaned_url = sanitize_youtube_url(url)
        yt = YouTube(cleaned_url)
        stream = yt.streams.get_highest_resolution()

        output_path = "downloads"
        os.makedirs(output_path, exist_ok=True)

        file_path = stream.download(output_path=output_path)
        filename = yt.title.replace(" ", "_") + ".mp4"

        return FileResponse(
            file_path,
            media_type="video/mp4",
            filename=filename,
            background=BackgroundTask(lambda: os.remove(file_path))  # auto-delete
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download video. Error: {str(e)}")
