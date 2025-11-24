"""
Video URL to Frames Node - Simple and Clean Implementation
Extracts all frames from video URL following Seed API pattern.
Based on ComfyUI-Seed-API video_to_frames_node.py
"""

import os
import torch
import requests
import tempfile
import numpy as np
import time
import subprocess
import re
from PIL import Image

# Try to import opencv - if not available, provide error message
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("WARNING: opencv-python not installed. Video frame extraction will not work.")
    print("To install: pip install opencv-python>=4.5.0")


def _fetch_video(url, timeout=300):
    """Download video content from URL with streaming and proper total timeout enforcement."""
    try:
        print(f"Starting video download from: {url}")
        print(f"Total timeout: {timeout} seconds")

        # Record start time for total timeout enforcement
        start_time = time.time()

        # Set headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'video/*, */*',
            'Accept-Encoding': 'identity',  # Disable compression to avoid issues
            'Connection': 'keep-alive'
        }

        # Start streaming request with connection timeout only
        try:
            response = requests.get(url, stream=True, timeout=30, headers=headers)  # 30s connection timeout only
            response.raise_for_status()  # Raise exception for bad status codes
        except requests.exceptions.Timeout:
            raise Exception("Connection timeout - could not connect to server within 30 seconds")

        # Check if we've already exceeded timeout during connection
        elapsed = time.time() - start_time
        if elapsed >= timeout:
            response.close()
            raise Exception(f"Total timeout exceeded during connection ({elapsed:.1f}s >= {timeout}s)")

        # Get file size if available
        total_size = response.headers.get('content-length')
        if total_size:
            total_size = int(total_size)
            print(f"Video size: {total_size / (1024*1024):.2f} MB")
        else:
            print("Video size: Unknown")

        print(f"Starting download, will timeout after {timeout} seconds...")

        # Download in chunks with strict total timeout enforcement
        video_content = bytearray()
        downloaded = 0
        chunk_size = 1024 * 1024  # 1MB chunks
        last_progress_logged = 0
        last_timeout_check = start_time

        try:
            for chunk in response.iter_content(chunk_size=chunk_size, decode_unicode=False):
                # Check total timeout every few chunks (not every single chunk for performance)
                current_time = time.time()
                if current_time - last_timeout_check > 5:  # Check every 5 seconds
                    elapsed = current_time - start_time
                    if elapsed >= timeout:
                        response.close()
                        raise Exception(f"Download timeout exceeded: {elapsed:.1f}s >= {timeout}s (downloaded {downloaded/(1024*1024):.2f} MB)")
                    last_timeout_check = current_time

                if chunk:
                    video_content.extend(chunk)
                    downloaded += len(chunk)

                    # Log progress every 10% or every 10MB, whichever comes first
                    if total_size:
                        progress = (downloaded / total_size) * 100
                        if progress - last_progress_logged >= 10:
                            elapsed = time.time() - start_time
                            print(f"Download progress: {progress:.1f}% ({downloaded / (1024*1024):.2f} MB) - {elapsed:.1f}s elapsed")
                            last_progress_logged = progress
                    else:
                        # Log every 10MB when size is unknown
                        mb_downloaded = downloaded / (1024*1024)
                        if mb_downloaded - last_progress_logged >= 10:
                            elapsed = time.time() - start_time
                            print(f"Downloaded: {mb_downloaded:.2f} MB - {elapsed:.1f}s elapsed")
                            last_progress_logged = mb_downloaded
        finally:
            response.close()

        final_elapsed = time.time() - start_time
        print(f"Download complete: {len(video_content)} bytes in {final_elapsed:.1f} seconds")
        return bytes(video_content)

    except requests.exceptions.Timeout:
        raise Exception(f"Download timeout after {timeout}s - video may be too large or connection too slow")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Download failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error during download: {str(e)}")


def _get_ffmpeg_path():
    """Find FFmpeg executable in common locations."""
    import shutil

    ffmpeg_paths = []

    # Try imageio_ffmpeg first (bundled with many ComfyUI installations)
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        imageio_ffmpeg_path = get_ffmpeg_exe()
        if imageio_ffmpeg_path and os.path.isfile(imageio_ffmpeg_path):
            ffmpeg_paths.append(imageio_ffmpeg_path)
    except ImportError:
        pass

    # Try system PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        ffmpeg_paths.append(system_ffmpeg)

    # Check ComfyUI root directory
    if os.path.isfile("ffmpeg"):
        ffmpeg_paths.append(os.path.abspath("ffmpeg"))
    if os.path.isfile("ffmpeg.exe"):
        ffmpeg_paths.append(os.path.abspath("ffmpeg.exe"))

    # Return first found path
    if ffmpeg_paths:
        return ffmpeg_paths[0]

    # If not found, return None to trigger helpful error
    return None


def _extract_audio(video_path):
    """
    Extract audio from video file using FFmpeg.
    Returns audio in ComfyUI format: {'waveform': tensor, 'sample_rate': int}
    """
    # Try to find ffmpeg
    ffmpeg_path = _get_ffmpeg_path()

    if ffmpeg_path is None:
        print("=" * 80)
        print("FFmpeg not found - cannot extract audio.")
        print("")
        print("To enable audio extraction, install FFmpeg:")
        print("  Option 1 (Easiest): pip install imageio-ffmpeg")
        print("  Option 2: Download from https://ffmpeg.org/download.html")
        print("            and add to system PATH or place in ComfyUI root")
        print("  Then restart ComfyUI")
        print("=" * 80)
        return {'waveform': torch.zeros((1, 1, 1), dtype=torch.float32), 'sample_rate': 44100}

    try:
        # Extract audio as raw f32le PCM data
        args = [
            ffmpeg_path, "-i", video_path,
            "-f", "f32le",  # 32-bit float little-endian PCM
            "-"  # Output to stdout
        ]

        # Run ffmpeg and capture output
        result = subprocess.run(
            args,
            capture_output=True,
            check=True
        )

        # Parse audio from stdout
        audio_data = torch.frombuffer(bytearray(result.stdout), dtype=torch.float32)

        # Parse stderr to get audio properties
        stderr_output = result.stderr.decode('utf-8', errors='ignore')

        # Extract sample rate and channels from FFmpeg output
        # Look for patterns like "44100 Hz, stereo" or "48000 Hz, mono"
        match = re.search(r', (\d+) Hz, (\w+)', stderr_output)

        if match:
            sample_rate = int(match.group(1))
            channel_type = match.group(2)
            channels = {"mono": 1, "stereo": 2}.get(channel_type, 2)
        else:
            # Default values if parsing fails
            sample_rate = 44100
            channels = 2

        # Reshape audio data: (total_samples,) -> (channels, samples_per_channel) -> (1, channels, samples_per_channel)
        if len(audio_data) > 0:
            audio_data = audio_data.reshape((-1, channels)).transpose(0, 1).unsqueeze(0)
        else:
            # No audio in video - return empty audio
            audio_data = torch.zeros((1, 1, 1), dtype=torch.float32)
            sample_rate = 44100

        return {'waveform': audio_data, 'sample_rate': sample_rate}

    except subprocess.CalledProcessError as e:
        # FFmpeg failed - video might not have audio
        stderr_output = e.stderr.decode('utf-8', errors='ignore') if e.stderr else ""
        if "Output file is empty" in stderr_output or "does not contain any stream" in stderr_output:
            print("Video does not contain an audio stream")
        else:
            print(f"Audio extraction failed (video may not have audio): {stderr_output}")
        # Return silent audio
        return {'waveform': torch.zeros((1, 1, 1), dtype=torch.float32), 'sample_rate': 44100}
    except Exception as e:
        print(f"Unexpected error extracting audio: {str(e)}")
        # Return silent audio
        return {'waveform': torch.zeros((1, 1, 1), dtype=torch.float32), 'sample_rate': 44100}


class VideoUrlToFramesNode:
    """
    Simple node that extracts all frames from a video URL as a tensor batch.
    Clean and focused approach following Seed API pattern.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_url": ("STRING", {"forceInput": True}),
            }
        }

    FUNCTION = "extract_frames"
    CATEGORY = "Sync.so"

    RETURN_TYPES = ("IMAGE", "AUDIO", "FLOAT", "INT")
    RETURN_NAMES = ("frames", "audio", "fps", "frame_count")

    def extract_frames(self, video_url):
        """
        Simple function that downloads video and extracts all frames and audio.
        
        Args:
            video_url: URL of the video to download
        
        Returns:
            frames: Extracted frames as IMAGE tensor batch
            audio: Audio track from the video in ComfyUI format
            fps: FPS of the video
            frame_count: Number of extracted frames
        """
        
        # Handle case where video_url might be a list
        if isinstance(video_url, list):
            video_url = video_url[0]
        
        # Initialize return values
        frames_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32)  # Default empty frames
        frame_count = 0
        video_fps = 0.0
        audio = {'waveform': torch.zeros((1, 1, 1), dtype=torch.float32), 'sample_rate': 44100}  # Default empty audio
        
        # Download video content (5 minute timeout)
        try:
            video_content = _fetch_video(video_url, timeout=300)
        except Exception as e:
            error_msg = str(e)
            print(f"Error downloading video: {error_msg}")

            # For ComfyUI services, throw error with video URL for user recovery
            # Format error message to include the video URL for easy copy/paste
            user_error = f"Video download failed: {error_msg}\n\n📋 VIDEO URL (copy to retry manually):\n{video_url}\n\n💡 Try: Download manually or check network connection"

            raise Exception(user_error)
        
        # Extract frames and audio
        if video_content:
            # Save video to temporary file for both frame and audio extraction
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                temp_file.write(video_content)
                temp_path = temp_file.name

            try:
                # Extract frames
                frames_tensor, frame_count, video_fps = self._extract_frames_from_file(temp_path)
                print(f"Extracted {frame_count} frames at {video_fps:.2f} fps")

                # Extract audio
                audio = _extract_audio(temp_path)
                if audio['waveform'].shape[2] > 1:  # Check if audio was actually extracted
                    print(f"Extracted audio: {audio['sample_rate']} Hz, {audio['waveform'].shape[1]} channel(s)")
                else:
                    print("No audio track found in video")

            except Exception as e:
                print(f"Error extracting frames/audio: {str(e)}")
                frames_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
                frame_count = 0
                video_fps = 0.0
                audio = {'waveform': torch.zeros((1, 1, 1), dtype=torch.float32), 'sample_rate': 44100}
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        return (frames_tensor, audio, video_fps, frame_count)
    
    def _extract_frames_from_file(self, video_path):
        """Extract all frames from video file as tensor batch."""
        if not OPENCV_AVAILABLE:
            print("Cannot extract frames: opencv-python not installed")
            return torch.zeros((1, 64, 64, 3), dtype=torch.float32), 0, 0.0

        # Open video with OpenCV
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise Exception("Could not open video file")

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        frames = []
        frame_count = 0

        print(f"Video info: {total_frames} total frames at {fps:.2f} fps")
        print(f"Extracting all frames...")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convert to PIL Image then to tensor
            pil_image = Image.fromarray(frame_rgb)
            frame_array = np.array(pil_image).astype(np.float32) / 255.0

            frames.append(frame_array)
            frame_count += 1

        cap.release()

        if frames:
            # Stack frames into tensor batch
            frames_tensor = torch.from_numpy(np.stack(frames, axis=0))
            print(f"Created tensor with shape: {frames_tensor.shape}")
        else:
            # Return empty tensor if no frames extracted
            frames_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
            frame_count = 0
            fps = 0.0

        return frames_tensor, frame_count, fps
