"""
Frames to Video with Audio Node - Combines processed frames with audio to create final video
Useful when frames are processed (upscale, filters, etc.) and need to be merged with original audio
"""

import os
import tempfile
import numpy as np
from typing import Optional


class VideoFromFile:
    """
    Wrapper class to create a VIDEO object compatible with ComfyUI.
    This mimics the interface expected by ComfyUI's Save Video node.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file = file_path
        self.filename = os.path.basename(file_path)
    
    def get_stream_source(self):
        """Return the file path for video streaming."""
        return self.file_path
    
    def get_dimensions(self):
        """Get video dimensions (width, height) using OpenCV."""
        try:
            import cv2
            cap = cv2.VideoCapture(self.file_path)
            if not cap.isOpened():
                raise Exception(f"Could not open video: {self.file_path}")
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            return (width, height)
        except Exception as e:
            # Fallback: return default dimensions if can't read
            print(f"Warning: Could not get video dimensions: {str(e)}")
            return (1920, 1080)  # Default fallback
    
    def save_to(self, output_path: str, filename_prefix: str = "", format: str = "auto", codec: str = "auto", metadata: dict = None, **kwargs):
        """
        Save video to specified path with given parameters.
        This method is called by ComfyUI's Save Video node.
        
        Args:
            output_path: Directory to save the video
            filename_prefix: Prefix for the filename
            format: Video format (auto, mp4, etc.)
            codec: Video codec (auto, h264, etc.)
            metadata: Optional metadata dictionary (ignored but accepted for compatibility)
            **kwargs: Additional parameters (ignored but accepted for compatibility)
        
        Returns:
            str: Path to the saved video file
        """
        import shutil
        import time
        
        # Create output directory if it doesn't exist
        os.makedirs(output_path, exist_ok=True)
        
        # Generate filename
        if filename_prefix:
            # Remove any path separators and clean up
            filename_prefix = filename_prefix.strip().replace(os.sep, "_")
            if not filename_prefix.endswith("_"):
                filename_prefix += "_"
        else:
            filename_prefix = ""
        
        # Generate timestamp-based filename
        timestamp = int(time.time())
        filename = f"{filename_prefix}{timestamp:05d}.mp4"
        
        # Full path for output
        output_file = os.path.join(output_path, filename)
        
        # Copy the video file to the output location
        # Since the video is already created, we just copy it
        shutil.copy2(self.file_path, output_file)
        
        print(f"Video saved to: {output_file}")
        return output_file


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
            
            # Convert PyTorch tensor to numpy array if needed
            # ComfyUI IMAGE format can be either torch.Tensor or numpy.ndarray
            if hasattr(images, 'cpu'):
                # It's a PyTorch tensor
                print("Converting PyTorch tensor to numpy array...")
                images = images.cpu().numpy()
            
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
            print(f"  Video dimensions: {width}x{height}")
            print(f"  FPS: {fps}")
            print(f"  Total frames: {batch_size}")
            
            # For large resolutions (> 1920x1080), use FFmpeg instead of OpenCV VideoWriter
            # OpenCV VideoWriter has limitations with very large resolutions
            max_opencv_resolution = 1920 * 1080 * 2  # 2x 1080p
            current_resolution = width * height
            
            if current_resolution > max_opencv_resolution:
                print(f"  → Large resolution detected ({width}x{height}), using FFmpeg for better compatibility...")
                try:
                    output_video_path = self._create_video_with_ffmpeg(images, width, height, fps, output_video_path, batch_size)
                except FileNotFoundError:
                    print(f"  ⚠ Warning: FFmpeg not found, falling back to OpenCV (may fail for large resolutions)...")
                    output_video_path = self._create_video_with_opencv(images, width, height, fps, output_video_path, batch_size)
            else:
                # Use OpenCV VideoWriter for smaller resolutions
                output_video_path = self._create_video_with_opencv(images, width, height, fps, output_video_path, batch_size)
            
            # Verify video file was created and has content
            if not os.path.exists(output_video_path):
                raise Exception(f"Video file was not created: {output_video_path}")
            
            file_size = os.path.getsize(output_video_path)
            if file_size < 1000:  # Less than 1KB is suspicious
                raise Exception(f"Video file is too small ({file_size} bytes) - video creation may have failed")
            
            print(f"✓ Video file size: {file_size / 1024 / 1024:.2f} MB")
            
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
            
            # Return VIDEO object (not just string path) for ComfyUI compatibility
            # Save Video node expects VIDEO object with get_dimensions() method
            video_obj = VideoFromFile(output_video_path)
            return (video_obj,)
            
        except Exception as e:
            error_msg = f"Error creating video from frames: {str(e)}"
            print(f"\n❌ ERROR: {error_msg}")
            raise Exception(error_msg) from e
    
    @staticmethod
    def _create_video_with_opencv(images, width, height, fps, output_path, batch_size):
        """Create video using OpenCV VideoWriter (for smaller resolutions)."""
        import cv2
        
        # Use H.264 codec for better compatibility
        fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 codec
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Verify VideoWriter is opened correctly
        if not out.isOpened():
            print(f"  ⚠ Warning: avc1 codec not available, trying mp4v...")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            if not out.isOpened():
                raise Exception(f"Could not initialize VideoWriter for {width}x{height} @ {fps}fps")
        
        frames_written = 0
        for i in range(batch_size):
            frame = images[i]
            
            # Ensure frame is numpy array
            if hasattr(frame, 'cpu'):
                frame = frame.cpu().numpy()
            
            # Check frame shape
            if len(frame.shape) != 3 or frame.shape[2] != 3:
                print(f"  ⚠ Warning: Frame {i} has unexpected shape: {frame.shape}, skipping...")
                continue
            
            # Ensure frame matches expected dimensions
            if frame.shape[0] != height or frame.shape[1] != width:
                frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)
            
            # Convert from float (0-1) to uint8 (0-255)
            if frame.dtype != np.uint8:
                if frame.max() > 1.0:
                    frame = np.clip(frame, 0, 1)
                frame = (frame * 255).astype(np.uint8)
            
            # Convert RGB to BGR for OpenCV
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Write frame
            success = out.write(frame_bgr)
            if success:
                frames_written += 1
            else:
                print(f"  ⚠ Warning: Failed to write frame {i}")
        
        out.release()
        print(f"✓ Video created with OpenCV: {output_path}")
        print(f"✓ Frames written: {frames_written}/{batch_size}")
        
        if frames_written == 0:
            raise Exception(f"Failed to write any frames. VideoWriter may not support {width}x{height} resolution.")
        
        return output_path
    
    @staticmethod
    def _create_video_with_ffmpeg(images, width, height, fps, output_path, batch_size):
        """Create video using FFmpeg (for large resolutions)."""
        import subprocess
        import tempfile
        
        # Create temporary directory for frames
        temp_dir = tempfile.mkdtemp()
        frame_pattern = os.path.join(temp_dir, "frame_%06d.png")
        
        try:
            print(f"  → Saving {batch_size} frames to temporary directory...")
            
            # Save all frames as PNG files
            for i in range(batch_size):
                frame = images[i]
                
                # Ensure frame is numpy array
                if hasattr(frame, 'cpu'):
                    frame = frame.cpu().numpy()
                
                # Check frame shape
                if len(frame.shape) != 3 or frame.shape[2] != 3:
                    continue
                
                # Ensure frame matches expected dimensions
                if frame.shape[0] != height or frame.shape[1] != width:
                    import cv2
                    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)
                
                # Convert from float (0-1) to uint8 (0-255)
                if frame.dtype != np.uint8:
                    if frame.max() > 1.0:
                        frame = np.clip(frame, 0, 1)
                    frame = (frame * 255).astype(np.uint8)
                
                # Save frame as PNG
                frame_path = os.path.join(temp_dir, f"frame_{i+1:06d}.png")
                import cv2
                # Convert RGB to BGR for OpenCV
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                cv2.imwrite(frame_path, frame_bgr)
            
            print(f"  → Frames saved, creating video with FFmpeg...")
            
            # Use FFmpeg to create video from frames
            # FFmpeg command: ffmpeg -framerate fps -i frame_%06d.png -c:v libx264 -pix_fmt yuv420p output.mp4
            ffmpeg_cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file
                '-framerate', str(fps),
                '-i', os.path.join(temp_dir, 'frame_%06d.png'),
                '-c:v', 'libx264',  # H.264 codec
                '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
                '-crf', '18',  # High quality
                output_path
            ]
            
            result = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg failed: {result.stderr}")
            
            print(f"✓ Video created with FFmpeg: {output_path}")
            print(f"✓ Frames processed: {batch_size}")
            
        finally:
            # Cleanup temporary frames
            import shutil
            try:
                shutil.rmtree(temp_dir)
                print(f"  → Temporary frames cleaned up")
            except:
                pass
        
        return output_path
    
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

