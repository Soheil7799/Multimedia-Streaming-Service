from fastapi import APIRouter, HTTPException
import subprocess
import json
import os
from app.api.endpoints.upload import get_videos

router = APIRouter()

@router.get("/{video_id}")
async def analyze_file(video_id: str):
    """
    Analyze an uploaded file and return its metadata.
    """
    videos = get_videos()
    if video_id not in videos:
        raise HTTPException(status_code=404, detail="Video not found")
    
    file_path = videos[video_id]["path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    # Use FFmpeg to analyze the file
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail="Failed to analyze file")
    
    # Parse the JSON output
    metadata = json.loads(result.stdout)
    
    # Extract relevant information
    file_info = {
        "id": video_id,
        "filename": videos[video_id]["filename"],
        "format": metadata.get("format", {}).get("format_name", "unknown"),
        "duration": float(metadata.get("format", {}).get("duration", 0)),
        "size": int(metadata.get("format", {}).get("size", 0)),
        "bit_rate": int(metadata.get("format", {}).get("bit_rate", 0)),
        "streams": []
    }
    
    # Extract stream information
    for stream in metadata.get("streams", []):
        stream_type = stream.get("codec_type")
        
        if stream_type == "video":
            file_info["streams"].append({
                "type": "video",
                "codec": stream.get("codec_name"),
                "width": stream.get("width"),
                "height": stream.get("height"),
                "frame_rate": eval(stream.get("r_frame_rate", "0/1")),  # Convert "24/1" to numeric
                "bit_depth": stream.get("bits_per_raw_sample"),
                "pixel_format": stream.get("pix_fmt")
            })
        elif stream_type == "audio":
            file_info["streams"].append({
                "type": "audio",
                "codec": stream.get("codec_name"),
                "channels": stream.get("channels"),
                "sample_rate": stream.get("sample_rate"),
                "bit_depth": stream.get("bits_per_sample")
            })
    
    # Add available filter options
    file_info["available_filters"] = {
        "audio": [
            {
                "name": "gain_compression",
                "display_name": "Gain Compression",
                "params": [
                    {"name": "threshold", "type": "range", "min": 0.1, "max": 1.0, "default": 0.5, "step": 0.1},
                    {"name": "ratio", "type": "range", "min": 1.0, "max": 20.0, "default": 4.0, "step": 0.5}
                ]
            },
            {
                "name": "voice_enhancement",
                "display_name": "Voice Enhancement",
                "params": [
                    {"name": "alpha", "type": "range", "min": 0.1, "max": 0.99, "default": 0.95, "step": 0.01}
                ]
            },
            {
                "name": "denoise_delay",
                "display_name": "Denoise & Delay",
                "params": [
                    {"name": "delay_ms", "type": "range", "min": 100, "max": 2000, "default": 500, "step": 100},
                    {"name": "decay", "type": "range", "min": 0.1, "max": 0.9, "default": 0.5, "step": 0.1},
                    {"name": "wiener_size", "type": "range", "min": 501, "max": 2001, "default": 1001, "step": 100}
                ]
            },
            {
                "name": "phone",
                "display_name": "Phone Effect",
                "params": []  # No adjustable parameters
            },
            {
                "name": "car",
                "display_name": "Car Effect",
                "params": []  # No adjustable parameters
            }
        ],
        "video": [
            {
                "name": "grayscale",
                "display_name": "Grayscale",
                "params": []  # No adjustable parameters
            },
            {
                "name": "color_invert",
                "display_name": "Color Invert",
                "params": []  # No adjustable parameters
            },
            {
                "name": "frame_interpolation",
                "display_name": "Frame Interpolation",
                "params": [
                    {"name": "target_fps", "type": "range", "min": 30, "max": 120, "default": 60, "step": 10}
                ]
            },
            {
                "name": "upscaling",
                "display_name": "Upscaling",
                "params": [
                    {"name": "width", "type": "number", "min": 640, "max": 3840, "default": 1920, "step": 1},
                    {"name": "height", "type": "number", "min": 480, "max": 2160, "default": 1080, "step": 1}
                ]
            }
        ]
    }
    
    return file_info