import os
import subprocess
import logging
from typing import List, Dict, Any
import tempfile

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoFilterManager:
    def __init__(self):
        """
        Initialize the video filter manager with available filters.
        """
        self.filters = {
            "grayscale": self._apply_grayscale,
            "color_invert": self._apply_color_invert,
            "frame_interpolation": self._apply_frame_interpolation,
            "upscaling": self._apply_upscaling
        }
        
        # Check if FFmpeg is installed
        try:
            subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
            logger.info("FFmpeg is installed and ready to use")
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("FFmpeg is not installed or not accessible. Video filters will not work.")
    
    def process_video(self, input_path: str, output_path: str, filters_config: List[Dict[str, Any]]) -> str:
        """
        Apply multiple video filters based on configuration.
        
        Parameters:
        - input_path: Path to the input video file
        - output_path: Path to save the processed video
        - filters_config: List of filter configurations
        
        Returns:
        - Path to the processed video file
        """
        logger.info(f"Starting video processing with {len(filters_config)} filters")
        
        # If no filters specified, just copy the input file
        if not filters_config:
            logger.info("No video filters specified, copying input file to output")
            try:
                # Use FFmpeg to copy the file without re-encoding
                cmd = [
                    "ffmpeg",
                    "-i", input_path,
                    "-c", "copy",
                    "-y",
                    output_path
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                return output_path
            except subprocess.SubprocessError as e:
                logger.error(f"Error copying file: {str(e)}")
                # Fall back to simple file copy
                import shutil
                shutil.copy2(input_path, output_path)
                return output_path
        
        # Create a temporary file path for intermediate processing
        temp_output = input_path
        final_output = output_path
        
        try:
                # Create a dedicated temp directory for intermediate files
            with tempfile.TemporaryDirectory() as temp_processing_dir:
                logger.info(f"Created temporary directory for filter processing: {temp_processing_dir}")
                
                # Apply each filter sequentially
                for i, filter_config in enumerate(filters_config):
                    filter_name = filter_config["name"]
                    params = filter_config.get("params", {})
                    
                    logger.info(f"Applying filter {i+1}/{len(filters_config)}: {filter_name}")
                    
                    if filter_name in self.filters:
                        filter_func = self.filters[filter_name]
                        
                        # For the last filter, use the final output path
                        if i == len(filters_config) - 1:
                            current_output = final_output
                        else:
                            # Use a temporary file for intermediate steps, always in the temp directory
                            current_output = os.path.join(temp_processing_dir, f"temp_{i}_{os.path.basename(output_path)}")
                        
                        # Apply the filter
                        logger.info(f"Processing from {temp_output} to {current_output}")
                        filter_func(temp_output, current_output, params)
                        
                        # Update the temp output for the next filter
                        if i < len(filters_config) - 1:
                            temp_output = current_output
                else:
                    logger.warning(f"Filter {filter_name} not found, skipping")
            
            logger.info("Video processing completed successfully")
            return final_output
            
        except Exception as e:
            logger.error(f"Error during video processing: {str(e)}")
            # If an error occurs, copy the original file to the output path
            logger.info("Falling back to original video due to processing error")
            import shutil
            shutil.copy2(input_path, output_path)
            return output_path
    
    def _apply_grayscale(self, input_path: str, output_path: str, params: Dict[str, Any]) -> None:
        """
        Apply grayscale effect using FFmpeg.
        
        Parameters:
        - input_path: Path to the input video file
        - output_path: Path to save the processed video
        - params: Filter parameters (not used for grayscale)
        """
        logger.info("Applying grayscale filter")
        try:
            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-vf", "format=gray",
                "-c:a", "copy",  # Copy audio stream without re-encoding
                "-y",  # Overwrite output file if it exists
                output_path
            ]
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info("Grayscale filter applied successfully")
        except subprocess.SubprocessError as e:
            logger.error(f"Error applying grayscale filter: {str(e)}")
            if hasattr(e, 'stderr'):
                logger.error(f"FFmpeg error: {e.stderr}")
            raise
    
    def _apply_color_invert(self, input_path: str, output_path: str, params: Dict[str, Any]) -> None:
        """
        Apply color inversion effect using FFmpeg.
        
        Parameters:
        - input_path: Path to the input video file
        - output_path: Path to save the processed video
        - params: Filter parameters (not used for color inversion)
        """
        logger.info("Applying color invert filter")
        try:
            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-vf", "negate",
                "-c:a", "copy",  # Copy audio stream without re-encoding
                "-y",  # Overwrite output file if it exists
                output_path
            ]
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info("Color invert filter applied successfully")
        except subprocess.SubprocessError as e:
            logger.error(f"Error applying color invert filter: {str(e)}")
            if hasattr(e, 'stderr'):
                logger.error(f"FFmpeg error: {e.stderr}")
            raise
    
    def _apply_frame_interpolation(self, input_path: str, output_path: str, params: Dict[str, Any]) -> None:
        """
        Apply frame interpolation to increase frames per second.
        
        Parameters:
        - input_path: Path to the input video file
        - output_path: Path to save the processed video
        - params: Filter parameters (target_fps: desired frames per second)
        """
        target_fps = params.get("target_fps", 60)
        logger.info(f"Applying frame interpolation filter with target FPS: {target_fps}")
        
        try:
            # First check if minterpolate filter is available
            filter_check = subprocess.run(
                ["ffmpeg", "-filters"], 
                check=True, 
                capture_output=True, 
                text=True
            )
            
            # Use simpler method if minterpolate not available
            if "minterpolate" not in filter_check.stdout:
                logger.warning("minterpolate filter not available, using fps filter instead")
                cmd = [
                    "ffmpeg",
                    "-i", input_path,
                    "-filter:v", f"fps={target_fps}",
                    "-c:a", "copy",
                    "-y",
                    output_path
                ]
            else:
                cmd = [
                    "ffmpeg",
                    "-i", input_path,
                    "-filter:v", f"minterpolate=fps={target_fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir",
                    "-c:a", "copy",  # Copy audio stream without re-encoding
                    "-y",  # Overwrite output file if it exists
                    output_path
                ]
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info("Frame interpolation filter applied successfully")
        except subprocess.SubprocessError as e:
            logger.error(f"Error applying frame interpolation filter: {str(e)}")
            if hasattr(e, 'stderr'):
                logger.error(f"FFmpeg error: {e.stderr}")
            
            # Fall back to simpler fps filter if minterpolate fails
            try:
                logger.info("Falling back to simpler fps filter")
                cmd = [
                    "ffmpeg",
                    "-i", input_path,
                    "-filter:v", f"fps={target_fps}",
                    "-c:a", "copy",
                    "-y",
                    output_path
                ]
                subprocess.run(cmd, check=True, capture_output=True)
            except subprocess.SubprocessError as e2:
                logger.error(f"Error with fallback fps filter: {str(e2)}")
                raise
    
    def _apply_upscaling(self, input_path: str, output_path: str, params: Dict[str, Any]) -> None:
        """
        Apply upscaling to increase video resolution.
        
        Parameters:
        - input_path: Path to the input video file
        - output_path: Path to save the processed video
        - params: Filter parameters (width, height: target dimensions)
        """
        width = params.get("width", 1920)
        height = params.get("height", 1080)
        logger.info(f"Applying upscaling filter to {width}x{height}")
        
        try:
            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-vf", f"scale={width}:{height}:flags=lanczos",
                "-c:a", "copy",  # Copy audio stream without re-encoding
                "-y",  # Overwrite output file if it exists
                output_path
            ]
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info("Upscaling filter applied successfully")
        except subprocess.SubprocessError as e:
            logger.error(f"Error applying upscaling filter: {str(e)}")
            if hasattr(e, 'stderr'):
                logger.error(f"FFmpeg error: {e.stderr}")
            
            # Try with simpler scaling method if lanczos fails
            try:
                logger.info("Falling back to simpler scaling method")
                cmd = [
                    "ffmpeg",
                    "-i", input_path,
                    "-vf", f"scale={width}:{height}",
                    "-c:a", "copy",
                    "-y",
                    output_path
                ]
                subprocess.run(cmd, check=True, capture_output=True)
            except subprocess.SubprocessError as e2:
                logger.error(f"Error with fallback scaling method: {str(e2)}")
                raise