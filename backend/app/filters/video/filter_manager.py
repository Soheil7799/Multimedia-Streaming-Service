import os
import subprocess
from typing import List, Dict, Any

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
        # If no filters specified, just return the input path
        if not filters_config:
            return input_path
        
        # Create a temporary file path for intermediate processing
        temp_output = input_path
        final_output = output_path
        
        # Apply each filter sequentially
        for i, filter_config in enumerate(filters_config):
            filter_name = filter_config["name"]
            params = filter_config.get("params", {})
            
            if filter_name in self.filters:
                filter_func = self.filters[filter_name]
                
                # For the last filter, use the final output path
                if i == len(filters_config) - 1:
                    current_output = final_output
                else:
                    # Use a temporary file for intermediate steps
                    temp_dir = os.path.dirname(output_path)
                    current_output = os.path.join(temp_dir, f"temp_{i}_{os.path.basename(output_path)}")
                
                # Apply the filter
                filter_func(temp_output, current_output, params)
                
                # Update the temp output for the next filter
                if i < len(filters_config) - 1:
                    temp_output = current_output
        
        return final_output
    
    def _apply_grayscale(self, input_path: str, output_path: str, params: Dict[str, Any]) -> None:
        """
        Apply grayscale effect using FFmpeg.
        
        Parameters:
        - input_path: Path to the input video file
        - output_path: Path to save the processed video
        - params: Filter parameters (not used for grayscale)
        """
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vf", "format=gray",
            "-c:a", "copy",  # Copy audio stream without re-encoding
            "-y",  # Overwrite output file if it exists
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
    
    def _apply_color_invert(self, input_path: str, output_path: str, params: Dict[str, Any]) -> None:
        """
        Apply color inversion effect using FFmpeg.
        
        Parameters:
        - input_path: Path to the input video file
        - output_path: Path to save the processed video
        - params: Filter parameters (not used for color inversion)
        """
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vf", "negate",
            "-c:a", "copy",  # Copy audio stream without re-encoding
            "-y",  # Overwrite output file if it exists
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
    
    def _apply_frame_interpolation(self, input_path: str, output_path: str, params: Dict[str, Any]) -> None:
        """
        Apply frame interpolation to increase frames per second.
        
        Parameters:
        - input_path: Path to the input video file
        - output_path: Path to save the processed video
        - params: Filter parameters (target_fps: desired frames per second)
        """
        target_fps = params.get("target_fps", 60)
        
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-filter_complex", f"minterpolate=fps={target_fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir",
            "-c:a", "copy",  # Copy audio stream without re-encoding
            "-y",  # Overwrite output file if it exists
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
    
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
        
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vf", f"scale={width}:{height}:flags=lanczos",
            "-c:a", "copy",  # Copy audio stream without re-encoding
            "-y",  # Overwrite output file if it exists
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)