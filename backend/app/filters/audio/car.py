import numpy as np
from scipy import signal

def apply_car_effect(audio_data, sample_rate):
    """
    Apply car effect:
    1. Stereo enhancement (side amplification)
    2. Low-pass filter (Butterworth), cut frequency: 10000 Hz
    
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
    
    # 1. Stereo enhancement (side amplification)
    if len(audio_float.shape) > 1 and audio_float.shape[1] > 1:  # Stereo
        # Calculate mid and side signals
        mid = (audio_float[:, 0] + audio_float[:, 1]) / 2
        side = (audio_float[:, 0] - audio_float[:, 1]) / 2
        
        # Amplify side signal (stereo width enhancement)
        side_amplified = side * 1.5  # Amplification factor
        
        # Reconstruct stereo from mid and amplified side
        enhanced = np.zeros_like(audio_float)
        enhanced[:, 0] = mid + side_amplified
        enhanced[:, 1] = mid - side_amplified
    else:  # Mono - convert to stereo
        if len(audio_float.shape) == 1:
            enhanced = np.column_stack([audio_float, audio_float])
        else:
            enhanced = np.column_stack([audio_float[:, 0], audio_float[:, 0]])
    
    # 2. Apply low-pass filter (cutoff at 10000 Hz)
    nyquist = 0.5 * sample_rate
    cutoff = 10000 / nyquist
    
    # Design Butterworth low-pass filter
    b, a = signal.butter(4, cutoff, btype='low')
    
    # Apply filter
    filtered = np.zeros_like(enhanced)
    for channel in range(enhanced.shape[1]):
        filtered[:, channel] = signal.filtfilt(b, a, enhanced[:, channel])
    
    # Normalize to prevent clipping
    max_val = np.max(np.abs(filtered))
    if max_val > 1.0:
        filtered = filtered / max_val
    
    return filtered