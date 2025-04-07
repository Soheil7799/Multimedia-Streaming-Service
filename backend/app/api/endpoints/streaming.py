from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import os
from app.api.endpoints.upload import get_videos

router = APIRouter()

@router.get("/{video_id}")
async def stream_video(video_id: str):
    """
    Stream a processed video.
    This must be possible after the filters have been successfully applied.
    """
    videos = get_videos()
    if video_id not in videos:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if not videos[video_id]["processed"]:
        raise HTTPException(status_code=400, detail="Video has not been processed yet")
    
    video_path = videos[video_id]["processed_path"]
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Processed video file not found")
    
    def iterfile():
        with open(video_path, mode="rb") as file_like:
            yield from file_like
    
    # Determine media type based on file extension
    # You might want to improve this with a proper mime type detection
    file_extension = os.path.splitext(video_path)[1].lower()
    media_type = "video/mp4"  # Default
    
    if file_extension == ".avi":
        media_type = "video/x-msvideo"
    elif file_extension == ".mkv":
        media_type = "video/x-matroska"
    elif file_extension == ".mov":
        media_type = "video/quicktime"
    
    return StreamingResponse(iterfile(), media_type=media_type)