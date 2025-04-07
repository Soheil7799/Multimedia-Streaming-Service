import os
import shutil
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
from app.core.config import settings
from app.api.endpoints.upload import get_videos
from app.filters.audio.filter_manager import AudioFilterManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    # Save the configuration
    videos[video_id]["config"] = config
    logger.info(f"Configuration saved for video {video_id}: {config}")
    
    return {"message": "Configuration saved successfully"}

@router.post("/{video_id}/apply")
async def apply_filters(video_id: str, background_tasks: BackgroundTasks):
    """
    Apply configured filters to the video or audio file.
    This must be possible if there is a previous file uploaded and filters have been configured.
    """
    videos = get_videos()
    if video_id not in videos:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not videos[video_id]["config"]:
        raise HTTPException(status_code=400, detail="No configuration saved. Configure filters first.")
    
    try:
        # Get the input and output paths
        input_file = videos[video_id]["path"]
        original_filename = os.path.basename(input_file)
        processed_filename = f"processed_{original_filename}"
        processed_path = os.path.join(settings.PROCESSED_DIR, processed_filename)
        
        # Ensure output directory exists
        os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
        
        logger.info(f"Applying filters to file: {input_file}")
        logger.info(f"Output will be saved to: {processed_path}")
        
        # Get the configuration
        config = videos[video_id]["config"]
        audio_filters = config.get("audio_filters", [])
        
        # Process audio only if there are audio filters to apply
        if audio_filters:
            logger.info(f"Applying {len(audio_filters)} audio filters: {[f['name'] for f in audio_filters]}")
            try:
                audio_filter_manager.process_video(input_file, processed_path, audio_filters)
            except Exception as e:
                logger.error(f"Error applying audio filters: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error applying audio filters: {str(e)}"
                )
        else:
            # If no audio filters, just copy the file
            logger.info(f"No audio filters to apply, copying file to: {processed_path}")
            try:
                shutil.copy2(input_file, processed_path)
            except Exception as e:
                logger.error(f"Error copying file: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error copying file: {str(e)}"
                )
        
        # Update video info
        videos[video_id]["processed"] = True
        videos[video_id]["processed_path"] = processed_path
        
        logger.info(f"Successfully applied filters to {video_id}")
        
        return {"message": "Filters applied successfully"}
    except Exception as e:
        logger.error(f"Unexpected error applying filters: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error applying filters: {str(e)}"
        )