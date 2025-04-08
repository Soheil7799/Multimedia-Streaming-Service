import numpy as np
import os
import tempfile
import logging
from app.filters.audio.gain_compression import apply_gain_compression
from app.filters.audio.voice_enhancement import apply_voice_enhancement
from app.filters.audio.denoise_delay import apply_denoise_delay
from app.filters.audio.phone import apply_phone_effect
from app.filters.audio.car import apply_car_effect
from app.filters.audio.utils import extract_audio_from_video, save_audio_to_wav, merge_audio_with_video

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioFilterManager:
    def __init__(self):
        self.filters = {
            "gain_compression": apply_gain_compression,
            "voice_enhancement": apply_voice_enhancement,
            "denoise_delay": apply_denoise_delay,
            "phone": apply_phone_effect,
            "car": apply_car_effect
        }
    
    def process_audio(self, audio_data, sample_rate, filters_config):
        """
        Apply multiple audio filters based on configuration.
        
        Parameters:
        - audio_data: Audio data as numpy array
        - sample_rate: Sample rate of the audio
        - filters_config: List of filter configurations
        
        Returns:
        - Processed audio data
        """
        processed = audio_data.astype(np.float32)
        
        # Normalize to -1 to 1 range if it's not already
        if processed.dtype != np.float32:
            processed = processed.astype(np.float32)
            if np.max(np.abs(processed)) > 1.0:
                processed = processed / 32767.0  # Assuming 16-bit audio
        
        # Apply each filter in sequence
        for filter_config in filters_config:
            filter_name = filter_config["name"]
            params = filter_config.get("params", {})
            
            logger.info(f"Applying audio filter: {filter_name}")
            
            if filter_name in self.filters:
                filter_func = self.filters[filter_name]
                
                try:
                    # Add sample_rate parameter if the filter needs it
                    if filter_name in ["voice_enhancement", "denoise_delay", "phone", "car"]:
                        params["sample_rate"] = sample_rate
                    
                    processed = filter_func(processed, **params)
                    logger.info(f"Successfully applied {filter_name} filter")
                except Exception as e:
                    logger.error(f"Error applying {filter_name} filter: {str(e)}")
                    # Continue with next filter rather than failing completely
            else:
                logger.warning(f"Skipping unknown audio filter: {filter_name}")
        
        return processed
    
    def process_video(self, input_path, output_path, filters_config):
        """
        Process the audio of a video file.
        
        Parameters:
        - input_path: Path to the input video file
        - output_path: Path to save the processed video
        - filters_config: List of filter configurations
        
        Returns:
        - Path to the processed video file
        """
        logger.info(f"Starting audio processing for {input_path}")
        
        if not filters_config:
            logger.info("No audio filters to apply, copying file")
            import shutil
            shutil.copy2(input_path, output_path)
            return output_path
        
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                logger.info(f"Created temp directory: {temp_dir}")
                
                # Extract audio from video
                try:
                    temp_wav, sample_rate, audio_data = extract_audio_from_video(input_path, temp_dir)
                    logger.info(f"Extracted audio: {sample_rate}Hz, shape: {audio_data.shape}")
                except Exception as e:
                    logger.error(f"Failed to extract audio: {str(e)}")
                    # If audio extraction fails, just copy the original video
                    import shutil
                    shutil.copy2(input_path, output_path)
                    return output_path
                
                # Process audio
                try:
                    processed_audio = self.process_audio(audio_data, sample_rate, filters_config)
                    logger.info("Audio processing completed successfully")
                except Exception as e:
                    logger.error(f"Error during audio processing: {str(e)}")
                    # If processing fails, use original audio
                    processed_audio = audio_data
                
                # Save processed audio
                processed_wav = os.path.join(temp_dir, "processed_audio.wav")
                try:
                    save_audio_to_wav(processed_audio, sample_rate, processed_wav)
                    logger.info(f"Saved processed audio to {processed_wav}")
                except Exception as e:
                    logger.error(f"Failed to save processed audio: {str(e)}")
                    # If saving fails, try to save original audio
                    save_audio_to_wav(audio_data, sample_rate, processed_wav)
                
                # Merge processed audio with original video
                try:
                    merge_audio_with_video(input_path, processed_wav, output_path)
                    logger.info(f"Merged audio with video to {output_path}")
                except Exception as e:
                    logger.error(f"Failed to merge audio with video: {str(e)}")
                    # If merging fails, just copy the original video
                    import shutil
                    shutil.copy2(input_path, output_path)
        
        except Exception as e:
            logger.error(f"Unexpected error in audio processing: {str(e)}")
            # Final fallback: copy the original video
            import shutil
            shutil.copy2(input_path, output_path)
        
        return output_path