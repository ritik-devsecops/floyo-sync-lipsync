"""
Video URL to Frames Node - Traditional ComfyUI Node Structure
Converts video URLs to ComfyUI IMAGE format following Seed API pattern.
This node can be used with any API node that outputs video URLs.
"""

import os
import numpy as np
import torch
from .video_url_utils import VideoUrlUtils


class VideoUrlToFramesNode:
    """
    Video URL to Frames Node for ComfyUI.
    
    Converts video URLs to ComfyUI IMAGE format by extracting frames.
    Follows the ComfyUI-Seed-API pattern for video URL processing.
    This node can be used with Sync.so Lipsync or any API node that outputs video URLs.
    
    Inputs:
        video_url (STRING): URL to the video file
        num_frames (INT): Number of frames to extract (evenly distributed)
        extraction_fps (FLOAT): Extract frames at specific FPS (optional, overrides num_frames)
    
    Outputs:
        images (IMAGE): Batch of extracted frames in ComfyUI IMAGE format
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        """
        Define input types for the node.
        
        Returns:
            dict: Dictionary containing input type definitions
        """
        return {
            "required": {
                "video_url": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Video URL to extract frames from."
                }),
                "extraction_mode": (["auto", "num_frames", "fps_based"], {
                    "default": "auto",
                    "tooltip": "Auto: Extract all frames at original FPS (recommended). num_frames: Extract specific number of frames. fps_based: Extract at specific FPS rate."
                }),
            },
            "optional": {
                "num_frames": ("INT", {
                    "default": 10,
                    "min": 1,
                    "max": 1000,
                    "step": 1,
                    "tooltip": "Number of frames to extract evenly. Only used when extraction_mode is 'num_frames'."
                }),
                "extraction_fps": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "max": 60.0,
                    "step": 0.1,
                    "tooltip": "Extract at specific FPS. Only used when extraction_mode is 'fps_based'. Example: 24.0 = extract at 24 FPS."
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "video_url")
    FUNCTION = "execute"
    CATEGORY = "Sync.so"
    DESCRIPTION = "Extract frames from video URL. Auto mode extracts all frames at original FPS (recommended). Returns frames and original video URL for audio extraction."
    
    def execute(self, video_url, extraction_mode="auto", num_frames=10, extraction_fps=0.0):
        """
        Execute video URL to frames conversion.
        
        Args:
            video_url: URL to the video file
            extraction_mode: "auto" (extract all at original FPS), "num_frames" (extract X frames), or "fps_based" (extract at specific FPS)
            num_frames: Number of frames to extract (only used when extraction_mode is "num_frames")
            extraction_fps: Extract frames at specific FPS (only used when extraction_mode is "fps_based")
        
        Returns:
            tuple: (image_array, video_url) - Extracted frames as IMAGE tensor and original video URL
        """
        try:
            # Validate input
            if not video_url or not video_url.strip():
                raise ValueError("video_url is required and cannot be empty")
            
            print(f"Converting video URL to frames...")
            print(f"Video URL: {video_url}")
            print(f"Extraction mode: {extraction_mode}")
            
            # Download video first to get properties (needed for auto mode)
            import tempfile
            temp_video_path = None
            
            if extraction_mode == "auto":
                # Auto mode: Extract all frames at original video FPS
                print(f"\n[AUTO MODE] Detecting video properties and extracting all frames...")
                
                # Download video once
                temp_video_path = VideoUrlUtils.download_video_from_url(video_url)
                
                # Get video FPS and properties
                import cv2
                cap = cv2.VideoCapture(temp_video_path)
                if not cap.isOpened():
                    raise Exception(f"Could not open video: {temp_video_path}")
                
                video_fps = cap.get(cv2.CAP_PROP_FPS)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.release()
                
                print(f"  → Video FPS: {video_fps}")
                print(f"  → Total frames: {total_frames}")
                print(f"  → Extracting all {total_frames} frames at original FPS ({video_fps})...")
                
                # Extract all frames using the already downloaded video
                frames = VideoUrlUtils.extract_frames_from_video(
                    temp_video_path,
                    fps=video_fps  # Extract at original FPS (will get all frames)
                )
                
                # Convert to ComfyUI format
                image_array, _ = VideoUrlUtils.frames_to_comfyui_image(frames)
                
                # Cleanup temp file
                if temp_video_path and os.path.exists(temp_video_path):
                    try:
                        os.remove(temp_video_path)
                        print(f"  → Temporary video cleaned up")
                    except:
                        pass
                
            elif extraction_mode == "fps_based":
                # FPS-based extraction
                if extraction_fps <= 0:
                    raise ValueError("extraction_fps must be > 0 when extraction_mode is 'fps_based'")
                
                print(f"Extraction FPS: {extraction_fps}")
                image_array, _ = VideoUrlUtils.video_url_to_frames(
                    video_url=video_url,
                    fps=extraction_fps,
                    keep_temp_file=False
                )
            else:
                # num_frames mode (default)
                print(f"Num frames: {num_frames}")
                image_array, _ = VideoUrlUtils.video_url_to_frames(
                    video_url=video_url,
                    num_frames=num_frames,
                    keep_temp_file=False
                )
            
            print(f"Successfully extracted {image_array.shape[0]} frames")
            print(f"Frame dimensions: {image_array.shape[1]}x{image_array.shape[2]}")
            
            # Convert numpy array to PyTorch tensor (ComfyUI IMAGE format requirement)
            # ComfyUI IMAGE format: torch.Tensor with shape [batch, height, width, channels]
            # Values should be in range 0.0 to 1.0 (float32)
            if isinstance(image_array, np.ndarray):
                print(f"Converting numpy array to PyTorch tensor...")
                # Ensure values are in 0-1 range (should already be normalized)
                if image_array.max() > 1.0:
                    image_array = image_array / 255.0
                
                # Convert to torch tensor
                image_tensor = torch.from_numpy(image_array).float()
                print(f"Converted to PyTorch tensor: {image_tensor.shape}, dtype: {image_tensor.dtype}")
            else:
                # Already a tensor, use as is
                image_tensor = image_array
            
            print(f"Original video URL preserved for audio extraction")
            print(f"Video URL to frames conversion completed!")
            
            # Return: frames as PyTorch tensor and original video URL (for audio extraction later)
            return (image_tensor, video_url)
            
        except ValueError as e:
            error_msg = f"Invalid input: {str(e)}"
            print(error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Error converting video URL to frames: {str(e)}"
            print(error_msg)
            raise Exception(error_msg) from e

