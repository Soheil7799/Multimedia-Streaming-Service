import numpy as np
from scipy import signal

def apply_denoise_delay(audio_data, sample_rate, delay_ms=500, decay=0.5, wiener_size=1001):
    """
    Apply denoising (Wiener filter) and add delay effect.
    
    Parameters:
    - audio_data: numpy array of audio samples
    - sample_rate: sampling rate of the audio
    - delay_ms: delay time in milliseconds
    - decay: decay factor for delayed signal (0 to 1)
    - wiener_size: size of the Wiener filter window
    
    Returns:
    - Processed audio data
    """
    # Convert to float for processing
    audio_float = audio_data.astype(np.float32)
    if np.max(np.abs(audio_float)) > 1.0:
        audio_float = audio_float / 32767.0  # Assuming 16-bit audio
    
    # Apply Wiener filter for denoising
    if len(audio_float.shape) > 1:  # Stereo
        denoised = np.zeros_like(audio_float)
        for channel in range(audio_float.shape[1]):
            denoised[:, channel] = signal.wiener(audio_float[:, channel], wiener_size)
    else:  # Mono
        denoised = signal.wiener(audio_float, wiener_size)
    
    # Add delay effect
    delay_samples = int(delay_ms * sample_rate / 1000)
    
    if len(denoised.shape) > 1:  # Stereo
        delayed = np.zeros_like(denoised)
        for channel in range(denoised.shape[1]):
            delayed[:, channel] = denoised[:, channel].copy()
            delayed[delay_samples:, channel] += decay * denoised[:-delay_samples, channel]
    else:  # Mono
        delayed = denoised.copy()
        delayed[delay_samples:] += decay * denoised[:-delay_samples]
    
    # Normalize to prevent clipping
    max_val = np.max(np.abs(delayed))
    if max_val > 1.0:
        delayed = delayed / max_val
    
    return delayed