import os
import subprocess
import numpy as np
import tempfile
from scipy.io import wavfile

def extract_audio_from_video(video_path, temp_dir=None):
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
    
    # Run FFmpeg
    subprocess.run(cmd, check=True, capture_output=True)
    
    # Read the WAV file
    sample_rate, audio_data = wavfile.read(temp_wav)
    
    return temp_wav, sample_rate, audio_data

def save_audio_to_wav(audio_data, sample_rate, output_path):
    """
    Save audio data to a WAV file.
    
    Parameters:
    - audio_data: Audio data as numpy array
    - sample_rate: Sample rate of the audio
    - output_path: Path to save the WAV file
    """
    # Convert to 16-bit PCM
    if audio_data.dtype != np.int16:
        audio_data = np.clip(audio_data, -1.0, 1.0)
        audio_data = (audio_data * 32767).astype(np.int16)
    
    wavfile.write(output_path, sample_rate, audio_data)

def merge_audio_with_video(video_path, audio_path, output_path):
    """
    Merge audio with video using FFmpeg.
    
    Parameters:
    - video_path: Path to the video file
    - audio_path: Path to the audio file
    - output_path: Path to save the merged video
    """
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
    
    subprocess.run(cmd, check=True, capture_output=True)