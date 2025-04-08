import os
import subprocess
import numpy as np
import tempfile
import logging
from scipy.io import wavfile

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_audio_from_video(file_path, temp_dir=None):
    """
    Extract audio from a video or audio file using FFmpeg.
    
    Parameters:
    - file_path: Path to the video or audio file
    - temp_dir: Directory to store temporary files
    
    Returns:
    - Path to the extracted WAV file
    - Sample rate
    - Audio data as numpy array
    """
    if temp_dir is None:
        temp_dir = tempfile.gettempdir()
    
    # Create a temporary WAV file
    temp_wav = os.path.join(temp_dir, f"temp_audio_{os.path.basename(file_path)}.wav")
    
    # FFmpeg command to extract audio
    cmd = [
        "ffmpeg",
        "-i", file_path,
        "-vn",  # No video
        "-acodec", "pcm_s16le",  # PCM 16-bit little-endian format
        "-ar", "44100",  # 44.1kHz sample rate
        "-ac", "2",  # Stereo
        "-y",  # Overwrite output file
        temp_wav
    ]
    
    logger.info(f"Executing FFmpeg command: {' '.join(cmd)}")
    
    try:
        # Run FFmpeg
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stderr:
            logger.info(f"FFmpeg output: {result.stderr}")
        
        # Read the WAV file
        sample_rate, audio_data = wavfile.read(temp_wav)
        logger.info(f"Successfully extracted audio: {sample_rate} Hz, shape: {audio_data.shape}")
        
        return temp_wav, sample_rate, audio_data
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e}")
        logger.error(f"FFmpeg stderr: {e.stderr}")
        raise RuntimeError(f"Failed to extract audio: {e.stderr}")
    except Exception as e:
        logger.error(f"Error extracting audio: {e}")
        raise

def save_audio_to_wav(audio_data, sample_rate, output_path):
    """
    Save audio data to a WAV file.
    
    Parameters:
    - audio_data: Audio data as numpy array
    - sample_rate: Sample rate of the audio
    - output_path: Path to save the WAV file
    """
    try:
        # Convert to 16-bit PCM
        if audio_data.dtype != np.int16:
            audio_data = np.clip(audio_data, -1.0, 1.0)
            audio_data = (audio_data * 32767).astype(np.int16)
        
        logger.info(f"Saving audio to: {output_path}, sample rate: {sample_rate}")
        wavfile.write(output_path, sample_rate, audio_data)
        logger.info("Audio saved successfully")
    except Exception as e:
        logger.error(f"Error saving audio: {e}")
        raise

def merge_audio_with_video(input_path, audio_path, output_path):
    """
    Merge audio with video using FFmpeg.
    Also handles cases where the input is an audio-only file.
    
    Parameters:
    - input_path: Path to the video or audio file
    - audio_path: Path to the processed audio file
    - output_path: Path to save the merged result
    """
    import subprocess
    import os
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Check if input is an audio-only file by extension
    audio_extensions = ['.mp3', '.wav', '.aac', '.ogg', '.flac', '.m4a']
    is_audio_only = any(input_path.lower().endswith(ext) for ext in audio_extensions)
    
    # Get output extension
    output_ext = os.path.splitext(output_path)[1].lower()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        if is_audio_only:
            # For MP3 output specifically
            if output_ext == '.mp3':
                cmd = [
                    "ffmpeg",
                    "-i", audio_path,
                    "-c:a", "libmp3lame",  # Use MP3 encoder
                    "-q:a", "2",           # Quality setting (0-9, 0=best, 9=worst)
                    "-y",                  # Overwrite output file
                    output_path
                ]
            # For AAC output
            elif output_ext in ['.m4a', '.aac']:
                cmd = [
                    "ffmpeg",
                    "-i", audio_path,
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-y",
                    output_path
                ]
            # For WAV output
            elif output_ext == '.wav':
                cmd = [
                    "ffmpeg",
                    "-i", audio_path,
                    "-c:a", "pcm_s16le",
                    "-y",
                    output_path
                ]
            # Default to MP3 if extension not recognized but use different name
            else:
                new_output_path = os.path.splitext(output_path)[0] + ".mp3"
                logger.warning(f"Unknown output extension: {output_ext}, using MP3 instead. Output will be saved to {new_output_path}")
                cmd = [
                    "ffmpeg",
                    "-i", audio_path,
                    "-c:a", "libmp3lame",
                    "-q:a", "2",
                    "-y",
                    new_output_path
                ]
                # Update the output_path for later reference
                output_path = new_output_path
        else:
            # For video files, check if the video contains a video stream
            probe_cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_type",
                "-of", "csv=p=0",
                input_path
            ]
            
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            has_video_stream = "video" in probe_result.stdout.strip()
            
            if has_video_stream:
                # If the file has a video stream, merge it with the processed audio
                cmd = [
                    "ffmpeg",
                    "-i", input_path,  # Input video
                    "-i", audio_path,  # Input processed audio
                    "-c:v", "copy",    # Copy video without re-encoding
                    "-c:a", "aac",     # Use AAC codec for audio
                    "-map", "0:v:0",   # Use first video stream from first input
                    "-map", "1:a:0",   # Use first audio stream from second input
                    "-shortest",       # Finish encoding when the shortest input stream ends
                    "-y",              # Overwrite output file
                    output_path
                ]
            else:
                # If the file doesn't have a video stream, treat it as audio-only
                # and repeat the audio-only logic
                if output_ext == '.mp3':
                    cmd = [
                        "ffmpeg",
                        "-i", audio_path,
                        "-c:a", "libmp3lame",
                        "-q:a", "2",
                        "-y",
                        output_path
                    ]
                else:
                    cmd = [
                        "ffmpeg",
                        "-i", audio_path,
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-y",
                        output_path
                    ]
        
        logger.info(f"Executing FFmpeg command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if result.stderr:
            logger.info(f"FFmpeg output: {result.stderr}")
            
        logger.info(f"Successfully created output file: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e}")
        logger.error(f"FFmpeg stderr: {e.stderr}")
        raise RuntimeError(f"Failed to process audio/video: {e.stderr}")
    except Exception as e:
        logger.error(f"Error processing audio/video: {e}")
        raise