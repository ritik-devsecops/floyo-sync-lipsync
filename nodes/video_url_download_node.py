"""
Video URL Download Node - Downloads video from URL and saves it locally
Useful for saving the output from Sync.so Lipsync node
"""

import os
from .sync_utils import SyncApiHandler


class VideoUrlDownloadNode:
    """
    Video URL Download Node for ComfyUI.
    
    Downloads video from URL and saves it to a local file.
    Useful for saving the output from Sync.so Lipsync node.
    
    Inputs:
        video_url (STRING): URL to the video file
        output_path (STRING): Optional path to save the video. If empty, saves to ComfyUI output folder.
        filename (STRING): Optional filename for the video. If empty, uses default name.
    
    Outputs:
        video (VIDEO): VIDEO type output - downloaded video file that can be used with Save Video node
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
                    "tooltip": "Video URL to download. Connect from Sync.so Lipsync output."
                }),
            },
            "optional": {
                "output_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Directory to save video. Leave empty to use default output folder."
                }),
                "filename": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Custom filename (without extension). Leave empty for auto-generated name."
                }),
            }
        }
    
    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    FUNCTION = "execute"
    CATEGORY = "Sync.so"
    OUTPUT_NODE = True
    DESCRIPTION = "Download video from URL and save it locally."
    
    def execute(self, video_url, output_path="", filename=""):
        """
        Execute video download from URL.
        
        Args:
            video_url: URL to the video file
            output_path: Directory path to save video (optional)
            filename: Custom filename without extension (optional)
        
        Returns:
            tuple: (video_path,) - Path to downloaded video file
        """
        try:
            # Validate input
            if not video_url or not video_url.strip():
                raise ValueError("video_url is required and cannot be empty")
            
            print("=" * 60)
            print("Video URL Download Node - Starting Download")
            print("=" * 60)
            print(f"Video URL: {video_url}")
            
            # Determine output directory
            if output_path and output_path.strip():
                save_dir = output_path.strip()
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir, exist_ok=True)
                    print(f"Created output directory: {save_dir}")
            else:
                # Use ComfyUI output folder (default)
                # Try to find ComfyUI output folder
                save_dir = os.path.join(os.getcwd(), "output")
                if not os.path.exists(save_dir):
                    save_dir = os.path.join(os.path.expanduser("~"), "ComfyUI", "output")
                if not os.path.exists(save_dir):
                    save_dir = os.getcwd()  # Fallback to current directory
                os.makedirs(save_dir, exist_ok=True)
                print(f"Using output directory: {save_dir}")
            
            # Determine filename
            if filename and filename.strip():
                video_filename = filename.strip()
                if not video_filename.endswith('.mp4'):
                    video_filename += '.mp4'
            else:
                # Generate default filename with timestamp
                import time
                timestamp = int(time.time())
                video_filename = f"sync_lipsync_output_{timestamp}.mp4"
            
            # Full path to save video
            full_path = os.path.join(save_dir, video_filename)
            
            print(f"Downloading video to: {full_path}")
            
            # Download video using SyncApiHandler
            downloaded_path = SyncApiHandler.download_file_from_url(video_url, suffix='.mp4', output_path=full_path)
            
            print("=" * 60)
            print(f"✓ Video downloaded successfully!")
            print(f"✓ Saved to: {downloaded_path}")
            print("=" * 60)
            
            # Return as VIDEO type - ComfyUI expects file path string for VIDEO type
            # This allows the output to be used with Save Video node or other video nodes
            return (downloaded_path,)
            
        except ValueError as e:
            error_msg = f"Invalid input: {str(e)}"
            print(f"\n❌ ERROR: {error_msg}")
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Error downloading video: {str(e)}"
            print(f"\n❌ ERROR: {error_msg}")
            raise Exception(error_msg) from e

