import os
import tempfile
from app.core.config import settings
from app.api.endpoints.upload import get_videos
from app.filters.audio.filter_manager import AudioFilterManager
from app.filters.video.filter_manager import VideoFilterManager
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import shutil

router = APIRouter()
audio_filter_manager = AudioFilterManager()
video_filter_manager = VideoFilterManager()

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
    video_filters = config.get("video_filters", [])
    
    # Create a temporary directory for intermediate processing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_video_path = os.path.join(temp_dir, "temp_video.mp4")
        
        # Process audio if audio filters are specified
        if audio_filters:
            # Process the video with audio filters and save to temporary path
            audio_filter_manager.process_video(input_file, temp_video_path, audio_filters)
            # Update input for video processing
            current_input = temp_video_path
        else:
            # Use original input file if no audio filters
            current_input = input_file
        
        # Process video if video filters are specified
        if video_filters:
            # Process the video with video filters and save to final path
            video_filter_manager.process_video(current_input, processed_path, video_filters)
        else:
            # If no video filters, copy the current input to the final path
            if current_input != input_file:  # Only copy if we processed audio
                shutil.copy2(current_input, processed_path)
            else:
                # No filters applied at all, just copy the original
                shutil.copy2(input_file, processed_path)
    
    # Update video info
    videos[video_id]["processed"] = True
    videos[video_id]["processed_path"] = processed_path
    
    return {"message": "Filters applied successfully"}