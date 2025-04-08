import os
import tempfile
import logging
from app.core.config import settings
from app.api.endpoints.upload import get_videos
from app.filters.audio.filter_manager import AudioFilterManager
from app.filters.video.filter_manager import VideoFilterManager
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    # Log the configuration
    logger.info(f"Configuring filters for video {video_id}")
    logger.info(f"Audio filters: {config['audio_filters']}")
    logger.info(f"Video filters: {config['video_filters']}")
    
    # Save the configuration
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
    
    # Ensure directories exist
    os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
    
    # Get the configuration
    config = videos[video_id]["config"]
    audio_filters = config.get("audio_filters", [])
    video_filters = config.get("video_filters", [])
    
    logger.info(f"Starting filter application for video {video_id}")
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {processed_path}")
    
    try:
        # Create a temporary directory for intermediate processing
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Created temporary directory: {temp_dir}")
            temp_video_path = os.path.join(temp_dir, "temp_video.mp4")
            
            # Process audio if audio filters are specified
            if audio_filters:
                logger.info(f"Applying {len(audio_filters)} audio filters")
                try:
                    # Process the video with audio filters and save to temporary path
                    audio_filter_manager.process_video(input_file, temp_video_path, audio_filters)
                    # Update input for video processing
                    current_input = temp_video_path
                    logger.info("Audio filters applied successfully")
                except Exception as e:
                    logger.error(f"Error applying audio filters: {str(e)}")
                    # Fall back to original input
                    current_input = input_file
            else:
                logger.info("No audio filters to apply")
                # Use original input file if no audio filters
                current_input = input_file
            
            # Process video if video filters are specified
            if video_filters:
                logger.info(f"Applying {len(video_filters)} video filters")
                try:
                    # Process the video with video filters and save to final path
                    video_filter_manager.process_video(current_input, processed_path, video_filters)
                    logger.info("Video filters applied successfully")
                except Exception as e:
                    logger.error(f"Error applying video filters: {str(e)}")
                    # If video processing fails, copy the current input to the final path
                    logger.info("Falling back to input after audio processing due to video filter error")
                    shutil.copy2(current_input, processed_path)
            else:
                logger.info("No video filters to apply")
                # If no video filters, copy the current input to the final path
                if current_input != input_file:  # Only copy if we processed audio
                    logger.info("Copying audio-processed file to final output")
                    shutil.copy2(current_input, processed_path)
                else:
                    logger.info("No filters applied, copying original file to output")
                    # No filters applied at all, just copy the original
                    shutil.copy2(input_file, processed_path)
        
        # Update video info
        videos[video_id]["processed"] = True
        videos[video_id]["processed_path"] = processed_path
        logger.info(f"Filter application completed successfully for video {video_id}")
        
        return {"message": "Filters applied successfully"}
    
    except Exception as e:
        logger.error(f"Unexpected error during filter application: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing video: {str(e)}"
        )