from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
import uuid
from app.core.config import settings

router = APIRouter()

# In-memory storage for simplicity (in a real app, this might be a database)
videos = {}

@router.post("", status_code=201)
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video file to the server.
    Only allowed if no video has been previously uploaded or if previous videos have been deleted.
    """
    # Check if we already have a video
    if videos:
        return JSONResponse(
            status_code=400,
            content={"message": "A file is already uploaded. Please delete it first."}
        )
    
    # Validate file format (basic validation)
    filename = file.filename
    if not any(filename.lower().endswith(f".{fmt}") for fmt in settings.ALLOWED_FORMATS):
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format. Allowed formats: {', '.join(settings.ALLOWED_FORMATS)}"
        )
    
    # Generate unique ID
    video_id = str(uuid.uuid4())
    
    # Save file
    file_location = os.path.join(settings.UPLOAD_DIR, f"{video_id}_{filename}")
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Store video info
    videos[video_id] = {
        "id": video_id,
        "filename": filename,
        "path": file_location,
        "processed": False,
        "config": {}
    }
    
    return {"id": video_id, "filename": filename}

@router.delete("/{video_id}")
async def delete_video(video_id: str):
    """
    Delete a previously uploaded video.
    Only possible if a video has been previously uploaded and not already deleted.
    """
    if video_id not in videos:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Remove the file
    file_path = videos[video_id]["path"]
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Remove processed file if exists
    processed_path = videos[video_id].get("processed_path")
    if processed_path and os.path.exists(processed_path):
        os.remove(processed_path)
    
    # Remove from storage
    del videos[video_id]
    
    return {"message": "Video deleted successfully"}

# Export videos dictionary to be accessible by other modules
def get_videos():
    return videos