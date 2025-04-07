import os
from app.core.config import settings
from app.api.endpoints.upload import get_videos
from app.filters.audio.filter_manager import AudioFilterManager
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import shutil






router = APIRouter()
audio_filter_manager = AudioFilterManager()

@router.post("/{video_id}/configure")
async def configure_filters(video_id: str, config: Dict[str, Any]):
    """
    Configure audio and video filters for a previously uploaded video.
    """
    videos = get_videos()
    if video_id not in videos:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Validate configuration (basic validation)
    if "audio_filters" not in config or "video_filters" not in config:
        raise HTTPException(
            status_code=400, 
            detail="Configuration must include both 'audio_filters' and 'video_filters'"
        )
    
    # Here you would validate the specific filters and parameters
    # For now, we'll just save the configuration
    videos[video_id]["config"] = config
    
    return {"message": "Configuration saved successfully"}

@router.post("/{video_id}/apply")
async def apply_filters(video_id: str, background_tasks: BackgroundTasks):
    """
    Apply configured filters to the video.
    This must be possible if there is a previous video uploaded and filters have been configured.
    """
    videos = get_videos()
    if video_id not in videos:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if not videos[video_id]["config"]:
        raise HTTPException(status_code=400, detail="No configuration saved. Configure filters first.")
    
    # Get the input and output paths
    input_file = videos[video_id]["path"]
    processed_filename = f"processed_{os.path.basename(input_file)}"
    processed_path = os.path.join(settings.PROCESSED_DIR, processed_filename)
    
    # Get the configuration
    config = videos[video_id]["config"]
    audio_filters = config.get("audio_filters", [])
    
    # Process audio
    if audio_filters:
        audio_filter_manager.process_video(input_file, processed_path, audio_filters)
    else:
        # If no audio filters, just copy the file for now
        import shutil
        shutil.copy2(input_file, processed_path)
    
    # Update video info
    videos[video_id]["processed"] = True
    videos[video_id]["processed_path"] = processed_path
    
    return {"message": "Filters applied successfully"}