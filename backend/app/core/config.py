import os
from typing import List

class Settings:
    # API settings
    API_PREFIX: str = "/api"
    DEBUG: bool = os.getenv("DEBUG", "1") == "1"
    
    # File settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    PROCESSED_DIR: str = os.getenv("PROCESSED_DIR", "processed")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "104857600"))  # 100MB
    ALLOWED_FORMATS: List[str] = os.getenv("ALLOWED_FORMATS", "mp4,avi,mov,mkv,mp3,wav,aac,ogg").split(",")    
    # Create required directories
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

settings = Settings()