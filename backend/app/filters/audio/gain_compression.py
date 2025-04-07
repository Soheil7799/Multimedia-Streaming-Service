import numpy as np

def apply_gain_compression(audio_data, threshold=0.5, ratio=4.0):
    """
    Apply gain compression to audio data.
    It emulates the behavior of analog amplifiers that have a saturation region.
    
    Parameters:
    - audio_data: numpy array of audio samples (normalized to -1.0 to 1.0)
    - threshold: compression threshold (0.0 to 1.0)
    - ratio: compression ratio
    
    Returns:
    - Processed audio data
    """
    # Create a copy to avoid modifying the original data
    compressed = np.copy(audio_data).astype(np.float32)
    
    # Normalize to -1 to 1 range if it's not already
    if compressed.dtype != np.float32:
        compressed = compressed.astype(np.float32)
        if np.max(np.abs(compressed)) > 1.0:
            compressed = compressed / 32767.0  # Assuming 16-bit audio
    
    # Find samples above threshold
    mask = np.abs(compressed) > threshold
    
    # Apply compression
    compressed[mask] = np.sign(compressed[mask]) * (
        threshold + (np.abs(compressed[mask]) - threshold) / ratio
    )
    
    return compressed