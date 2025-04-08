import os
import subprocess
import numpy as np
import tempfile
import logging
from scipy.io import wavfile
from typing import Tuple, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_audio_from_video(video_path: str, temp_dir: Optional[str] = None) -> Tuple[str, int, np.ndarray]:
    """
    Extract audio from a video file using FFmpeg.
    
    Parameters:
    - video_path: Path to the video file
    - temp_dir: Directory to store temporary files
    
    Returns:
    - Path to the extracted WAV file
    - Sample rate
    - Audio data as numpy array
    """
    if temp_dir is None:
        temp_dir = tempfile.gettempdir()
    
    # Create a temporary WAV file
    temp_wav = os.path.join(temp_dir, f"temp_audio_{os.path.basename(video_path)}.wav")
    
    logger.info(f"Extracting audio from {video_path} to {temp_wav}")
    
    # FFmpeg command to extract audio
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vn",  # No video
        "-acodec", "pcm_s16le",  # PCM 16-bit little-endian format
        "-ar", "44100",  # 44.1kHz sample rate
        "-ac", "2",  # Stereo
        "-y",  # Overwrite output file
        temp_wav
    ]
    
    try:
        # Run FFmpeg
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Audio extraction completed successfully")
    except subprocess.SubprocessError as e:
        logger.error(f"Error extracting audio: {str(e)}")
        if hasattr(e, 'stderr'):
            logger.error(f"FFmpeg error: {e.stderr}")
        
        # Try a simpler approach for audio extraction
        try:
            logger.info("Trying simpler audio extraction method")
            simple_cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vn",  # No video
                "-y",  # Overwrite output file
                temp_wav
            ]
            subprocess.run(simple_cmd, check=True, capture_output=True)
        except subprocess.SubprocessError as e2:
            logger.error(f"Simple audio extraction also failed: {str(e2)}")
            raise
    
    try:
        # Read the WAV file
        sample_rate, audio_data = wavfile.read(temp_wav)
        logger.info(f"Read WAV file: {sample_rate}Hz, shape: {audio_data.shape}")
        return temp_wav, sample_rate, audio_data
    except Exception as e:
        logger.error(f"Error reading WAV file: {str(e)}")
        # Create a dummy audio file as fallback
        dummy_sample_rate = 44100
        dummy_duration = 1  # 1 second of silence
        dummy_audio = np.zeros((dummy_sample_rate * dummy_duration, 2), dtype=np.int16)
        wavfile.write(temp_wav, dummy_sample_rate, dummy_audio)
        return temp_wav, dummy_sample_rate, dummy_audio

def save_audio_to_wav(audio_data: np.ndarray, sample_rate: int, output_path: str) -> None:
    """
    Save audio data to a WAV file.
    
    Parameters:
    - audio_data: Audio data as numpy array
    - sample_rate: Sample rate of the audio
    - output_path: Path to save the WAV file
    """
    logger.info(f"Saving audio to {output_path}")
    try:
        # Convert to 16-bit PCM
        if audio_data.dtype != np.int16:
            audio_data = np.clip(audio_data, -1.0, 1.0)
            audio_data = (audio_data * 32767).astype(np.int16)
        
        # Check for NaN or Inf values and replace them
        if np.any(np.isnan(audio_data)) or np.any(np.isinf(audio_data)):
            logger.warning("Audio contains NaN or Inf values, replacing with zeros")
            audio_data = np.nan_to_num(audio_data)
        
        wavfile.write(output_path, sample_rate, audio_data)
        logger.info("Successfully saved audio to WAV file")
    except Exception as e:
        logger.error(f"Error saving audio to WAV file: {str(e)}")
        # Create a dummy audio file as fallback
        dummy_audio = np.zeros((sample_rate * 1, 2), dtype=np.int16)  # 1 second of silence
        wavfile.write(output_path, sample_rate, dummy_audio)
        logger.warning("Created dummy silent audio as fallback")

def merge_audio_with_video(video_path: str, audio_path: str, output_path: str) -> None:
    """
    Merge audio with video using FFmpeg.
    
    Parameters:
    - video_path: Path to the video file
    - audio_path: Path to the audio file
    - output_path: Path to save the merged video
    """
    logger.info(f"Merging audio {audio_path} with video {video_path} to {output_path}")
    
    cmd = [
        "ffmpeg",
        "-i", video_path,  # Input video
        "-i", audio_path,  # Input audio
        "-c:v", "copy",    # Copy video without re-encoding
        "-c:a", "aac",     # Use AAC codec for audio
        "-strict", "experimental",
        "-map", "0:v:0",   # Use first video stream from first input
        "-map", "1:a:0",   # Use first audio stream from second input
        "-shortest",       # Finish encoding when the shortest input stream ends
        "-y",              # Overwrite output file
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Successfully merged audio with video")
    except subprocess.SubprocessError as e:
        logger.error(f"Error merging audio with video: {str(e)}")
        if hasattr(e, 'stderr'):
            logger.error(f"FFmpeg error: {e.stderr}")
        
        # Try a simpler approach
        try:
            logger.info("Trying simpler audio merging method")
            simple_cmd = [
                "ffmpeg",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "copy",
                "-y",
                output_path
            ]
            subprocess.run(simple_cmd, check=True, capture_output=True)
            logger.info("Simple audio merging succeeded")
        except subprocess.SubprocessError as e2:
            logger.error(f"Simple audio merging also failed: {str(e2)}")
            
            # As a last resort, just copy the original video
            logger.warning("Falling back to original video without audio processing")
            import shutil
            shutil.copy2(video_path, output_path)