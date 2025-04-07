import numpy as np
from scipy import signal

def apply_voice_enhancement(audio_data, sample_rate, alpha=0.95):
    """
    Apply voice enhancement filter:
    1. Pre-emphasis filter: y[n] = x[n] – α·x[n-1]
    2. Band-pass filter (Butterworth) in the range 800-6000 Hz
    
    Parameters:
    - audio_data: numpy array of audio samples
    - sample_rate: sampling rate of the audio
    - alpha: pre-emphasis coefficient (0 to 1)
    
    Returns:
    - Processed audio data
    """
    # Convert to float for processing
    audio_float = audio_data.astype(np.float32)
    if np.max(np.abs(audio_float)) > 1.0:
        audio_float = audio_float / 32767.0  # Assuming 16-bit audio
    
    # 1. Apply pre-emphasis filter: y[n] = x[n] – α·x[n-1]
    pre_emphasized = np.zeros_like(audio_float)
    pre_emphasized[0] = audio_float[0]
    for i in range(1, len(audio_float)):
        pre_emphasized[i] = audio_float[i] - alpha * audio_float[i-1]
    
    # 2. Apply band-pass filter (800-6000 Hz)
    nyquist = 0.5 * sample_rate
    low = 800 / nyquist
    high = 6000 / nyquist
    
    # Design Butterworth band-pass filter
    b, a = signal.butter(4, [low, high], btype='band')
    
    # Apply filter
    if len(audio_float.shape) > 1:  # Stereo
        enhanced = np.zeros_like(pre_emphasized)
        for channel in range(audio_float.shape[1]):
            enhanced[:, channel] = signal.filtfilt(b, a, pre_emphasized[:, channel])
    else:  # Mono
        enhanced = signal.filtfilt(b, a, pre_emphasized)
    
    return enhanced