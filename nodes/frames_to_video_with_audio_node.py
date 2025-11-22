"""
Frames to Video with Audio Node - Combines processed frames with audio to create final video
Useful when frames are processed (upscale, filters, etc.) and need to be merged with original audio
"""

import os
import tempfile
import numpy as np
from typing import Optional


class FramesToVideoWithAudioNode:
    """
    Frames to Video with Audio Node for ComfyUI.
    
    Combines processed frames (IMAGE) with audio to create final video.
    Useful when frames are processed (upscale, filters, etc.) and need original audio.
    
    Inputs:
        images (IMAGE): Processed frames in ComfyUI IMAGE format
        audio (AUDIO or STRING): Audio file or video URL with audio
        video_url (STRING, optional): Video URL to extract audio from
        fps (FLOAT): Output video FPS (default: 30.0)
        output_path (STRING, optional): Directory to save video
    
    Outputs:
        video (VIDEO): Final video with processed frames and audio
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {
                    "tooltip": "Processed frames from image processing nodes."
                }),
                "fps": ("FLOAT", {
                    "default": 30.0,
                    "min": 1.0,
                    "max": 120.0,
                    "step": 0.1,
                    "tooltip": "Output video frame rate (FPS)."
                }),
            },
            "optional": {
                "audio": ("AUDIO", {
                    "tooltip": "Audio to merge with video. Connect from LoadAudio node (recommended)."
                }),
                "video_url": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Video URL to extract audio from. Use if audio not connected. Connect from Video URL to Frames output."
                }),
                "output_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Directory to save video. Leave empty for default output folder."
                }),
            }
        }
    
    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    FUNCTION = "execute"
    CATEGORY = "Sync.so"
    OUTPUT_NODE = True
    DESCRIPTION = "Create video from processed frames and merge with audio. Connect audio from LoadAudio or provide video_url."
    
    def execute(self, images, fps=30.0, audio=None, video_url="", output_path=""):
        """
        Combine processed frames with audio to create final video.
        
        Args:
            images: Processed frames in IMAGE format [batch, height, width, channels]
            fps: Output video frame rate
            audio: Audio file (optional, if video_url provided)
            video_url: Video URL to extract audio from (optional)
            output_path: Directory to save video (optional)
        
        Returns:
            tuple: (video_path,) - Path to final video with audio
        """
        try:
            import cv2
            from .file_utils import FileUtils
            from .sync_utils import SyncApiHandler
            
            print("=" * 60)
            print("Frames to Video with Audio - Starting")
            print("=" * 60)
            
            # Validate inputs
            if images is None or len(images) == 0:
                raise ValueError("No frames provided")
            
            batch_size, height, width, channels = images.shape
            print(f"Frames: {batch_size}, Resolution: {width}x{height}")
            print(f"Target FPS: {fps}")
            
            # Determine output path
            if output_path and output_path.strip():
                save_dir = output_path.strip()
            else:
                save_dir = os.path.join(os.getcwd(), "output")
                if not os.path.exists(save_dir):
                    save_dir = os.path.join(os.path.expanduser("~"), "ComfyUI", "output")
                if not os.path.exists(save_dir):
                    save_dir = tempfile.gettempdir()
            
            os.makedirs(save_dir, exist_ok=True)
            
            import time
            timestamp = int(time.time())
            output_video_path = os.path.join(save_dir, f"processed_video_{timestamp}.mp4")
            
            # Convert frames to video
            print(f"\nCreating video from frames...")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
            
            for i in range(batch_size):
                frame = images[i]
                # Convert from float (0-1) to uint8 (0-255)
                if frame.dtype != np.uint8:
                    frame = (frame * 255).astype(np.uint8)
                # Convert RGB to BGR for OpenCV
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                out.write(frame_bgr)
            
            out.release()
            print(f"✓ Video created: {output_video_path}")
            
            # Handle audio
            audio_path = None
            if audio is not None:
                print(f"\nExtracting audio from AUDIO input...")
                try:
                    audio_path = FileUtils.get_audio_path(audio)
                    print(f"✓ Audio path: {audio_path}")
                except Exception as e:
                    print(f"⚠ Warning: Could not extract audio from AUDIO input: {str(e)}")
                    audio_path = None
            
            if not audio_path and video_url and video_url.strip():
                print(f"\nExtracting audio from video URL...")
                print(f"  Video URL: {video_url}")
                try:
                    # Download video temporarily to extract audio
                    temp_video = SyncApiHandler.download_file_from_url(video_url, suffix=".mp4")
                    print(f"  → Video downloaded for audio extraction")
                    audio_path = self._extract_audio_from_video(temp_video)
                    # Cleanup temp video
                    try:
                        os.remove(temp_video)
                        print(f"  → Temporary video cleaned up")
                    except:
                        pass
                    print(f"✓ Audio extracted from video URL")
                except Exception as e:
                    print(f"⚠ Warning: Could not extract audio from video URL: {str(e)}")
                    if "FFmpeg not found" in str(e):
                        print(f"  → Install FFmpeg: brew install ffmpeg (Mac) or apt install ffmpeg (Linux)")
                    print(f"  → Video will be saved without audio")
            
            # Merge audio with video if available
            if audio_path and os.path.exists(audio_path):
                print(f"\nMerging audio with video...")
                try:
                    final_video_path = self._merge_audio_with_video(
                        output_video_path, 
                        audio_path, 
                        save_dir,
                        timestamp
                    )
                    # Remove video without audio
                    try:
                        os.remove(output_video_path)
                    except:
                        pass
                    output_video_path = final_video_path
                    print(f"✓ Audio merged successfully")
                except Exception as e:
                    print(f"⚠ Warning: Could not merge audio: {str(e)}")
                    print(f"  → Video saved without audio")
            else:
                print(f"\n⚠ No audio provided - video saved without audio")
                print(f"  → Provide audio input or video_url to include audio")
            
            print("=" * 60)
            print(f"✓ Final video saved: {output_video_path}")
            print("=" * 60)
            
            return (output_video_path,)
            
        except Exception as e:
            error_msg = f"Error creating video from frames: {str(e)}"
            print(f"\n❌ ERROR: {error_msg}")
            raise Exception(error_msg) from e
    
    @staticmethod
    def _extract_audio_from_video(video_path: str) -> str:
        """Extract audio from video file using ffmpeg."""
        try:
            import subprocess
            
            audio_path = video_path.replace('.mp4', '.wav').replace('.mov', '.wav')
            
            # Use ffmpeg to extract audio
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '44100', '-ac', '2',
                '-y', audio_path
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=300
            )
            
            if result.returncode == 0 and os.path.exists(audio_path):
                return audio_path
            else:
                raise Exception(f"FFmpeg error: {result.stderr}")
                
        except FileNotFoundError:
            raise Exception("FFmpeg not found. Install FFmpeg to extract audio from video.")
        except Exception as e:
            raise Exception(f"Error extracting audio: {str(e)}")
    
    @staticmethod
    def _merge_audio_with_video(video_path: str, audio_path: str, output_dir: str, timestamp: int) -> str:
        """Merge audio with video using ffmpeg."""
        try:
            import subprocess
            
            final_video_path = os.path.join(output_dir, f"final_video_with_audio_{timestamp}.mp4")
            
            # Use ffmpeg to merge audio
            cmd = [
                'ffmpeg', '-i', video_path, '-i', audio_path,
                '-c:v', 'copy', '-c:a', 'aac',
                '-map', '0:v:0', '-map', '1:a:0',
                '-shortest', '-y', final_video_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0 and os.path.exists(final_video_path):
                return final_video_path
            else:
                raise Exception(f"FFmpeg error: {result.stderr}")
                
        except FileNotFoundError:
            raise Exception("FFmpeg not found. Install FFmpeg to merge audio with video.")
        except Exception as e:
            raise Exception(f"Error merging audio: {str(e)}")

