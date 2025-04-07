import numpy as np
from scipy import signal

def apply_phone_effect(audio_data, sample_rate):
    """
    Apply phone effect:
    1. Mono enhancement (side attenuation)
    2. Band Pass Filter (Butterworth) 800-12000 Hz
    
    Parameters:
    - audio_data: numpy array of audio samples
    - sample_rate: sampling rate of the audio
    
    Returns:
    - Processed audio data
    """
    # Convert to float for processing
    audio_float = audio_data.astype(np.float32)
    if np.max(np.abs(audio_float)) > 1.0:
        audio_float = audio_float / 32767.0  # Assuming 16-bit audio
    
    # 1. Mono enhancement (side attenuation)
    if len(audio_float.shape) > 1 and audio_float.shape[1] > 1:  # Stereo
        # Create mono signal (average of channels)
        mono = np.mean(audio_float, axis=1)
        
        # Create the processed audio (mono)
        processed = np.column_stack([mono, mono])
    else:
        processed = audio_float
    
    # 2. Apply band-pass filter (800-12000 Hz)
    nyquist = 0.5 * sample_rate
    low = 800 / nyquist
    high = 12000 / nyquist
    
    # Design Butterworth band-pass filter
    b, a = signal.butter(4, [low, high], btype='band')
    
    # Apply filter
    if len(processed.shape) > 1:  # Stereo
        filtered = np.zeros_like(processed)
        for channel in range(processed.shape[1]):
            filtered[:, channel] = signal.filtfilt(b, a, processed[:, channel])
    else:  # Mono
        filtered = signal.filtfilt(b, a, processed)
    
    return filtered