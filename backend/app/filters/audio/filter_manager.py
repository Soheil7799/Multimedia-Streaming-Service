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
        try:
            processed = audio_data.astype(np.float32)
            
            # Normalize to -1 to 1 range if it's not already
            if np.max(np.abs(processed)) > 1.0:
                processed = processed / 32767.0  # Assuming 16-bit audio
            
            logger.info(f"Processing audio with {len(filters_config)} filters")
            
            # Apply each filter in sequence
            for filter_config in filters_config:
                filter_name = filter_config["name"]
                params = filter_config.get("params", {})
                
                logger.info(f"Applying filter: {filter_name} with params: {params}")
                
                if filter_name in self.filters:
                    filter_func = self.filters[filter_name]
                    
                    # Add sample_rate parameter if the filter needs it
                    if filter_name in ["voice_enhancement", "denoise_delay", "phone", "car"]:
                        params["sample_rate"] = sample_rate
                    
                    processed = filter_func(processed, **params)
                else:
                    logger.warning(f"Unknown filter: {filter_name}")
            
            return processed
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            raise
    
    def process_video(self, input_path, output_path, filters_config):
        """
        Process the audio of a video file.
        
        Parameters:
        - input_path: Path to the input video or audio file
        - output_path: Path to save the processed output
        - filters_config: List of filter configurations
        
        Returns:
        - Path to the processed file
        """
        logger.info(f"Processing file: {input_path}")
        logger.info(f"Output will be saved to: {output_path}")
        
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract audio from input file
                logger.info("Extracting audio...")
                temp_wav, sample_rate, audio_data = extract_audio_from_video(input_path, temp_dir)
                
                logger.info(f"Audio extracted: {sample_rate} Hz, shape: {audio_data.shape}")
                
                # Process audio
                logger.info("Processing audio...")
                processed_audio = self.process_audio(audio_data, sample_rate, filters_config)
                
                # Save processed audio
                processed_wav = os.path.join(temp_dir, "processed_audio.wav")
                logger.info(f"Saving processed audio to: {processed_wav}")
                save_audio_to_wav(processed_audio, sample_rate, processed_wav)
                
                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Merge processed audio with original video or convert to output format
                logger.info("Merging audio with video or converting to output format...")
                merge_audio_with_video(input_path, processed_wav, output_path)
                
                logger.info("Processing completed successfully")
            
            return output_path
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise