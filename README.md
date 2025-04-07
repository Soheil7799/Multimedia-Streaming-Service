# Multimedia Streaming Service

A web service for uploading, processing, and streaming audio/video files with customizable filters.\
Final Project for the course "Music and multimedia streaming over the Internet".

## Project Overview

This project implements a web service that allows users to:

1. Upload a video file
2. Configure audio and video filters
3. Apply the selected filters to the video
4. Stream the processed video in the browser

The system applies audio filters implemented in Python and video filters using FFmpeg.

## Features

- **Video Upload**: Upload and manage a single video file
- **Audio Filters** (implemented in Python):
  - Gain compression
  - Voice enhancement (pre-emphasis + band-pass filtering)
  - Noise reduction (Wiener filter) with delay effect
  - Phone effect (mono enhancement + band-pass filtering)
  - Car effect (stereo enhancement + low-pass filtering)
- **Video Filters** (implemented with FFmpeg):
  - Grayscale conversion
  - Color inversion
  - Frame interpolation (increased FPS)
  - Upscaling (increased resolution)
- **Real-time Streaming**: Stream the processed video directly in the browser

## Technology Stack

- **Backend**: Python with FastAPI
- **Audio Processing**: SciPy, NumPy, and custom Python implementations
- **Video Processing**: FFmpeg
- **Frontend**: HTML, CSS, JavaScript
- **Containerization**: Docker
- **Deployment**: AWS EC2 and ECR
- **CI/CD**: GitHub Actions

## Project Requirements

This project follows the requirements specified in the course project description, including:

- Implementation of audio filters in Python 
- Implementation of video filters using FFmpeg 
- HTTP server implementation with specific endpoints
- Filter configuration and application as separate steps
- Video streaming capabilities

## License

[MIT License](LICENSE)

## Contributors

- Mostafa Shirvani
