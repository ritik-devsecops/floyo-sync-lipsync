"""
Video URL Utilities for handling video URLs and frame extraction.
Based on ComfyUI-Seed-API pattern for video URL to frames conversion.
This utility helps convert video URLs to ComfyUI compatible formats.
"""

import os
import tempfile
import requests
import numpy as np
from typing import Optional, List, Tuple


class VideoUrlUtils:
    """
    Utility class for handling video URLs and extracting frames.
    Follows the ComfyUI-Seed-API pattern for video URL processing.
    """

    @staticmethod
    def download_video_from_url(video_url: str, output_path: Optional[str] = None) -> str:
        """
        Download video from URL to a local file.
        
        Args:
            video_url: URL to the video file
            output_path: Optional path to save the video. If None, creates temp file.
        
        Returns:
            str: Path to the downloaded video file
        """
        try:
            print(f"Downloading video from URL: {video_url}")
            
            if output_path is None:
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                output_path = temp_file.name
                temp_file.close()
            
            # Download with streaming
            response = requests.get(video_url, stream=True, timeout=300)
            response.raise_for_status()
            
            # Write to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"Video downloaded successfully to: {output_path}")
            return output_path
            
        except Exception as e:
            error_msg = f"Error downloading video from URL {video_url}: {str(e)}"
            print(error_msg)
            raise Exception(error_msg) from e

    @staticmethod
    def extract_frames_from_video(
        video_path: str,
        num_frames: Optional[int] = None,
        frame_indices: Optional[List[int]] = None,
        fps: Optional[float] = None
    ) -> List[np.ndarray]:
        """
        Extract frames from video file.
        
        Args:
            video_path: Path to the video file
            num_frames: Number of frames to extract (evenly distributed)
            frame_indices: Specific frame indices to extract (if provided, num_frames ignored)
            fps: Frames per second for extraction (if provided)
        
        Returns:
            List of numpy arrays representing frames (shape: [H, W, 3])
        """
        try:
            import cv2
            
            print(f"Extracting frames from video: {video_path}")
            
            # Open video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception(f"Could not open video file: {video_path}")
            
            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            print(f"Video properties: {total_frames} frames, {video_fps} fps, {width}x{height}")
            
            frames = []
            
            if frame_indices is not None:
                # Extract specific frames
                for frame_idx in sorted(frame_indices):
                    if frame_idx < total_frames:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                        ret, frame = cap.read()
                        if ret:
                            # Convert BGR to RGB
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            frames.append(frame_rgb)
                        else:
                            print(f"Warning: Could not read frame {frame_idx}")
            elif num_frames is not None:
                # Extract evenly distributed frames
                if num_frames >= total_frames:
                    # Extract all frames
                    step = 1
                else:
                    step = total_frames // num_frames
                
                for i in range(0, total_frames, step):
                    if len(frames) >= num_frames:
                        break
                    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                    ret, frame = cap.read()
                    if ret:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frames.append(frame_rgb)
            elif fps is not None:
                # Extract frames at specific FPS
                frame_interval = int(video_fps / fps) if fps < video_fps else 1
                frame_idx = 0
                while frame_idx < total_frames:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                    ret, frame = cap.read()
                    if ret:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frames.append(frame_rgb)
                    frame_idx += frame_interval
            else:
                # Extract first frame only
                ret, frame = cap.read()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frames.append(frame_rgb)
            
            cap.release()
            
            print(f"Extracted {len(frames)} frames from video")
            return frames
            
        except ImportError:
            raise Exception("OpenCV (cv2) is required for frame extraction. Install with: pip install opencv-python")
        except Exception as e:
            error_msg = f"Error extracting frames from video: {str(e)}"
            print(error_msg)
            raise Exception(error_msg) from e

    @staticmethod
    def frames_to_comfyui_image(
        frames: List[np.ndarray]
    ) -> Tuple[np.ndarray, List[int]]:
        """
        Convert frames to ComfyUI IMAGE format.
        ComfyUI IMAGE format: numpy array of shape [batch, height, width, channels]
        
        Args:
            frames: List of numpy arrays (H, W, 3) representing frames
        
        Returns:
            Tuple of (image_array, shape_info) compatible with ComfyUI IMAGE format
        """
        try:
            if not frames:
                raise Exception("No frames provided")
            
            # Get dimensions
            h, w, c = frames[0].shape
            batch_size = len(frames)
            
            # Normalize to 0-1 range (if needed)
            normalized_frames = []
            for frame in frames:
                if frame.dtype == np.uint8:
                    # Normalize from 0-255 to 0-1
                    frame_float = frame.astype(np.float32) / 255.0
                else:
                    frame_float = frame.astype(np.float32)
                normalized_frames.append(frame_float)
            
            # Stack frames into batch format [batch, height, width, channels]
            image_array = np.stack(normalized_frames, axis=0)
            
            print(f"Converted {batch_size} frames to ComfyUI format: {image_array.shape}")
            
            # Shape info for reference: [batch, height, width, channels]
            shape_info = [batch_size, h, w, c]
            
            return image_array, shape_info
            
        except Exception as e:
            error_msg = f"Error converting frames to ComfyUI format: {str(e)}"
            print(error_msg)
            raise Exception(error_msg) from e

    @staticmethod
    def video_url_to_frames(
        video_url: str,
        num_frames: Optional[int] = None,
        frame_indices: Optional[List[int]] = None,
        fps: Optional[float] = None,
        keep_temp_file: bool = False
    ) -> Tuple[np.ndarray, str]:
        """
        Complete workflow: Download video from URL and extract frames.
        Returns ComfyUI compatible IMAGE format.
        
        Args:
            video_url: URL to the video file
            num_frames: Number of frames to extract
            frame_indices: Specific frame indices to extract
            fps: Frames per second for extraction
            keep_temp_file: Whether to keep the downloaded file (for debugging)
        
        Returns:
            Tuple of (image_array in ComfyUI format, temp_file_path)
        """
        temp_file_path = None
        try:
            # Step 1: Download video
            temp_file_path = VideoUrlUtils.download_video_from_url(video_url)
            
            # Step 2: Extract frames
            frames = VideoUrlUtils.extract_frames_from_video(
                temp_file_path,
                num_frames=num_frames,
                frame_indices=frame_indices,
                fps=fps
            )
            
            # Step 3: Convert to ComfyUI format
            image_array, shape_info = VideoUrlUtils.frames_to_comfyui_image(frames)
            
            # Cleanup temp file if not keeping
            if not keep_temp_file and temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    print(f"Cleaned up temporary video file: {temp_file_path}")
                except Exception as e:
                    print(f"Warning: Could not delete temp file {temp_file_path}: {str(e)}")
            
            return image_array, temp_file_path if keep_temp_file else None
            
        except Exception as e:
            # Cleanup on error
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except:
                    pass
            raise

