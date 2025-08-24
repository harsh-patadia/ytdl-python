from fastapi import FastAPI, Query, HTTPException
from pytube import YouTube
from fastapi.responses import FileResponse
import os

app = FastAPI()

@app.get("/download")
def download_video(url: str = Query(..., description="YouTube video URL")):
    try:
        yt = YouTube(url)
        stream = yt.streams.get_highest_resolution()

        # Set download path
        output_path = "downloads"
        os.makedirs(output_path, exist_ok=True)

        # Download video
        file_path = stream.download(output_path=output_path)

        # Return video file as download
        return FileResponse(file_path, media_type='video/mp4', filename=yt.title + ".mp4")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")
