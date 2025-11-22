"""
Video URL to Frames Node - Traditional ComfyUI Node Structure
Converts video URLs to ComfyUI IMAGE format following Seed API pattern.
This node can be used with any API node that outputs video URLs.
"""

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
                "num_frames": ("INT", {
                    "default": 10,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "tooltip": "Number of frames to extract evenly. Example: 10 = 10 frames throughout video. Leave default for most cases."
                }),
            },
            "optional": {
                "extraction_fps": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "max": 30.0,
                    "step": 0.1,
                    "tooltip": "Extract at specific FPS (overrides num_frames). Example: 1.0 = 1 frame/second. Set 0.0 to use num_frames instead."
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "video_url")
    FUNCTION = "execute"
    CATEGORY = "Sync.so"
    DESCRIPTION = "Extract frames from video URL for image processing. Returns frames and original video URL for audio extraction."
    
    def execute(self, video_url, num_frames=10, extraction_fps=0.0):
        """
        Execute video URL to frames conversion.
        
        Args:
            video_url: URL to the video file
            num_frames: Number of frames to extract (evenly distributed)
            extraction_fps: Extract frames at specific FPS (optional, overrides num_frames if > 0)
        
        Returns:
            tuple: (image_array,) - Extracted frames as IMAGE tensor
        """
        try:
            # Validate input
            if not video_url or not video_url.strip():
                raise ValueError("video_url is required and cannot be empty")
            
            print(f"Converting video URL to frames...")
            print(f"Video URL: {video_url}")
            
            # Extract frames from video URL
            # Use extraction_fps if provided, otherwise use num_frames
            if extraction_fps and extraction_fps > 0:
                print(f"Extraction FPS: {extraction_fps}")
                image_array, _ = VideoUrlUtils.video_url_to_frames(
                    video_url=video_url,
                    fps=extraction_fps,
                    keep_temp_file=False
                )
            else:
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

