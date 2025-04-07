import numpy as np
import os
import tempfile
from app.filters.audio.gain_compression import apply_gain_compression
from app.filters.audio.voice_enhancement import apply_voice_enhancement
from app.filters.audio.denoise_delay import apply_denoise_delay
from app.filters.audio.phone import apply_phone_effect
from app.filters.audio.car import apply_car_effect
from app.filters.audio.utils import extract_audio_from_video, save_audio_to_wav, merge_audio_with_video

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
            
            if filter_name in self.filters:
                filter_func = self.filters[filter_name]
                
                # Add sample_rate parameter if the filter needs it
                if filter_name in ["voice_enhancement", "denoise_delay", "phone", "car"]:
                    params["sample_rate"] = sample_rate
                
                processed = filter_func(processed, **params)
        
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
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract audio from video
            temp_wav, sample_rate, audio_data = extract_audio_from_video(input_path, temp_dir)
            
            # Process audio
            processed_audio = self.process_audio(audio_data, sample_rate, filters_config)
            
            # Save processed audio
            processed_wav = os.path.join(temp_dir, "processed_audio.wav")
            save_audio_to_wav(processed_audio, sample_rate, processed_wav)
            
            # Merge processed audio with original video
            merge_audio_with_video(input_path, processed_wav, output_path)
        
        return output_path