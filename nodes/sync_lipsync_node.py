"""
Sync.so Lipsync Node for ComfyUI - Traditional Node Structure
Provides video lipsync capabilities via Sync.so API integration.
Follows Seed API pattern for Floyo platform.

This node accepts VIDEO and AUDIO inputs directly from LoadVideo/LoadAudio nodes,
or STRING inputs (file paths or URLs) as fallback.
"""

import os
import json
import tempfile
import time
from .sync_utils import SyncApiHandler
from .sync_config import SyncConfig
from .file_utils import FileUtils


class SyncLipsyncNode:
    """
    Sync.so Lipsync Node for ComfyUI.
    
    This node takes video and audio inputs and generates a lip-synced video
    using the Sync.so API. Follows Seed API pattern - accepts VIDEO/AUDIO types
    directly from LoadVideo/LoadAudio nodes, or STRING inputs (paths/URLs).
    
    Inputs:
        video (VIDEO or STRING): VIDEO object from LoadVideo node, or file path/URL string
        audio (AUDIO or STRING): AUDIO object from LoadAudio node, or file path/URL string
        model (COMBO): Model to use (lipsync-2, lipsync-1.9.0-beta, lipsync-2-pro)
        sync_mode (COMBO): How to handle mismatched video/audio duration
        temperature (FLOAT): Temperature parameter (0.0-2.0, optional)
        active_speaker_detection (COMBO): Enable/disable active speaker detection
        start_time (FLOAT): Start time in seconds for video trimming (optional)
        end_time (FLOAT): End time in seconds for video trimming (optional)
        occlusion_detection (COMBO): Enable/disable occlusion detection
        segment_secs (FLOAT): Segment video in seconds for processing (optional)
        segment_frames (INT): Segment video in frames for processing (optional)
    
    Outputs:
        output_video_url (STRING): URL to the generated lip-synced video (always returned, Floyo compatible)
        video (VIDEO, optional): Downloaded video file for preview (only if download_for_preview enabled)
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
                "video": ("VIDEO", {
                    "tooltip": "Video file to sync. Connect from LoadVideo node."
                }),
                "audio": ("AUDIO", {
                    "tooltip": "Audio file to sync with video. Connect from LoadAudio node."
                }),
                "model": (["lipsync-2", "lipsync-1.9.0-beta", "lipsync-2-pro"], {
                    "default": "lipsync-2",
                    "tooltip": "Lipsync model to use. lipsync-2 recommended for best quality."
                }),
                "sync_mode": (["bounce", "loop", "cut_off", "silence", "remap"], {
                    "default": "remap",
                    "tooltip": "How to handle different video/audio lengths. remap adjusts video speed to match audio."
                }),
            },
            "optional": {
                "temperature": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "tooltip": "Controls generation randomness. Lower = more conservative, Higher = more creative."
                }),
                "active_speaker_detection": (["enable", "disable"], {
                    "default": "disable",
                    "tooltip": "Automatically detect active speakers in video. Requires Creator tier or higher."
                }),
                "start_time": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "step": 0.1,
                    "tooltip": "Start time in seconds. Use 0 for full video."
                }),
                "end_time": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "step": 0.1,
                    "tooltip": "End time in seconds. Use 0 for full video."
                }),
                "occlusion_detection": (["enable", "disable"], {
                    "default": "disable",
                    "tooltip": "Detect when face is blocked or occluded."
                }),
                "segment_secs": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "step": 1.0,
                    "tooltip": "Segment video by time (seconds). Use 0 to disable. Example: 10 = 10-second segments. Use for videos > 60 seconds."
                }),
                "segment_frames": ("INT", {
                    "default": 0,
                    "min": 0,
                    "step": 1,
                    "tooltip": "Segment video by frame count. Use 0 to disable. Example: 300 = 300-frame segments. Alternative to segment_secs."
                }),
                "download_for_preview": (["enable", "disable"], {
                    "default": "disable",
                    "tooltip": "Download video for preview. Keep disabled for platform compatibility."
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "VIDEO")
    RETURN_NAMES = ("output_video_url", "video")
    FUNCTION = "execute"
    CATEGORY = "Sync.so"
    DESCRIPTION = "Generate lip-synced videos from video and audio inputs using Sync.so API."
    
    def execute(
        self,
        video,
        audio,
        model,
        sync_mode,
        temperature=1.0,
        active_speaker_detection="disable",
        start_time=0.0,
        end_time=0.0,
        occlusion_detection="disable",
        segment_secs=0.0,
        segment_frames=0,
        download_for_preview="disable",
    ):
        """
        Execute lipsync generation using Sync.so API.
        
        This method follows Seed API pattern:
        1. Extracts file paths from VIDEO/AUDIO objects using FileUtils
        2. Handles both local files and URLs
        3. Uploads to Sync.so API
        4. Polls until completion
        5. Returns output video URL
        
        Args:
            video: VIDEO object from LoadVideo node, or file path/URL string
            audio: AUDIO object from LoadAudio node, or file path/URL string
            model: Model to use for lipsync
            sync_mode: How to handle mismatched video/audio duration
            temperature: Temperature parameter (0.0-2.0)
            active_speaker_detection: Enable/disable active speaker detection
            start_time: Start time in seconds (0.0 = no trimming)
            end_time: End time in seconds (0.0 = no trimming)
            occlusion_detection: Enable/disable occlusion detection
            segment_secs: Segment video in seconds (0.0 = disabled)
            segment_frames: Segment video in frames (0 = disabled)
        
        Returns:
            tuple: (output_video_url,) - URL to generated video
        """
        try:
            print("=" * 60)
            print("Sync.so Lipsync Node - Starting Generation")
            print("=" * 60)
            
            # ============================================================
            # STEP 1: EXTRACT FILE PATHS FROM VIDEO/AUDIO INPUTS
            # ============================================================
            # FileUtils handles:
            # - VIDEO/AUDIO objects (from LoadVideo/LoadAudio nodes)
            # - File path strings (local files)
            # - URL strings (remote files)
            print("\nSTEP 1: Extracting file paths from inputs...")
            print("-" * 60)
            
            video_path = FileUtils.get_video_path(video)
            print(f"✓ Video path extracted: {video_path}")
            print(f"  Type: {'URL' if video_path.startswith(('http://', 'https://')) else 'Local file'}")
            
            audio_path = FileUtils.get_audio_path(audio)
            print(f"✓ Audio path extracted: {audio_path}")
            print(f"  Type: {'URL' if audio_path.startswith(('http://', 'https://')) else 'Local file'}")
            
            # ============================================================
            # STEP 2: PREPARE PARAMETERS FOR API CALL
            # ============================================================
            print("\nSTEP 2: Preparing parameters for API call...")
            print("-" * 60)
            print(f"Model: {model}")
            print(f"Sync mode: {sync_mode}")
            
            # Determine if paths are local files or URLs
            video_is_local = os.path.exists(video_path) and not video_path.startswith(('http://', 'https://'))
            audio_is_local = os.path.exists(audio_path) and not audio_path.startswith(('http://', 'https://'))
            
            # Prepare parameters for API handler
            video_path_param = video_path if video_is_local else None
            video_url_param = video_path if not video_is_local else None
            audio_path_param = audio_path if audio_is_local else None
            audio_url_param = audio_path if not audio_is_local else None
            
            # Convert optional parameters
            temp_param = float(temperature) if temperature and temperature > 0 else None
            active_speaker_bool = active_speaker_detection == "enable" if active_speaker_detection else None
            start_time_param = float(start_time) if start_time and start_time > 0 else None
            end_time_param = float(end_time) if end_time and end_time > 0 else None
            occlusion_bool = occlusion_detection == "enable" if occlusion_detection else None
            segment_secs_param = float(segment_secs) if segment_secs and segment_secs > 0 else None
            segment_frames_param = int(segment_frames) if segment_frames and segment_frames > 0 else None
            
            if temp_param:
                print(f"Temperature: {temp_param}")
            if active_speaker_bool:
                print(f"Active speaker detection: enabled")
            if start_time_param:
                print(f"Start time: {start_time_param}s")
            if end_time_param:
                print(f"End time: {end_time_param}s")
            # Note: occlusion_detection parameter is kept in UI for future compatibility
            # but is not currently sent to Sync.so API as it's not supported
            # if occlusion_bool:
            #     print(f"Occlusion detection: enabled")
            if segment_secs_param:
                print(f"Segment seconds: {segment_secs_param}s")
            if segment_frames_param:
                print(f"Segment frames: {segment_frames_param}")
            
            # ============================================================
            # STEP 3: SUBMIT GENERATION REQUEST
            # ============================================================
            print("\nSTEP 3: Submitting generation request to Sync.so API...")
            print("-" * 60)
            
            result = SyncApiHandler.create_generation(
                video_path=video_path_param,
                video_url=video_url_param,
                audio_path=audio_path_param,
                audio_url=audio_url_param,
                model=model,
                sync_mode=sync_mode,
                temperature=temp_param,
                active_speaker_detection=active_speaker_bool,
                start_time=start_time_param,
                end_time=end_time_param,
                # occlusion_detection parameter not sent to API (not supported by Sync.so API)
                # occlusion_detection=occlusion_bool,
                segment_secs=segment_secs_param,
                segment_frames=segment_frames_param,
            )
            
            # Get generation ID
            generation_id = result.get("id")
            if not generation_id:
                raise Exception("No generation ID returned from API. Response: " + str(result))
            
            print(f"✓ Generation created with ID: {generation_id}")
            
            # ============================================================
            # STEP 4: WAIT FOR COMPLETION (POLLING)
            # ============================================================
            print("\nSTEP 4: Waiting for generation to complete...")
            print("-" * 60)
            print("Polling API every 5 seconds...")
            
            final_result = SyncApiHandler.wait_for_completion(generation_id)
            
            # ============================================================
            # STEP 5: EXTRACT OUTPUT URL
            # ============================================================
            print("\nSTEP 5: Extracting output URL...")
            print("-" * 60)
            
            output_url = (
                final_result.get("outputUrl")
                or final_result.get("output_url")
                or final_result.get("output")
            )
            if not output_url:
                raise Exception(
                    "Generation completed but no output URL found in response. "
                    "Response: " + str(final_result)
                )
            
            print("=" * 60)
            print("✓ Generation completed successfully!")
            print(f"✓ Output video URL: {output_url}")
            print("=" * 60)
            
            # ============================================================
            # STEP 6: DOWNLOAD VIDEO FOR PREVIEW (OPTIONAL)
            # ============================================================
            # Only download if explicitly enabled (for Floyo compatibility)
            # Floyo platform works with URLs, so video download is optional
            if download_for_preview == "enable":
                print("\nSTEP 6: Downloading video for preview...")
                print("-" * 60)
                
                try:
                    # Create temp file in ComfyUI output directory for preview
                    timestamp = int(time.time())
                    temp_filename = f"sync_lipsync_preview_{timestamp}.mp4"
                    
                    # Try to use ComfyUI output directory
                    output_dir = os.path.join(os.getcwd(), "output")
                    if not os.path.exists(output_dir):
                        output_dir = os.path.join(os.path.expanduser("~"), "ComfyUI", "output")
                    if not os.path.exists(output_dir):
                        output_dir = tempfile.gettempdir()
                    
                    os.makedirs(output_dir, exist_ok=True)
                    preview_path = os.path.join(output_dir, temp_filename)
                    
                    # Download video for preview
                    print(f"  → Downloading video to: {preview_path}")
                    downloaded_path = SyncApiHandler.download_file_from_url(
                        output_url, 
                        suffix='.mp4',
                        output_path=preview_path
                    )
                    
                    print(f"  ✓ Video downloaded for preview: {downloaded_path}")
                    print("=" * 60)
                    
                    # Return both URL (for Floyo/API) and VIDEO (for preview)
                    return (output_url, downloaded_path)
                    
                except Exception as preview_error:
                    # If preview download fails, still return URL (Floyo compatible)
                    print(f"  ⚠ Warning: Could not download video for preview: {str(preview_error)}")
                    print(f"  → Returning URL only (Floyo compatible). Use Video URL Download node to save video.")
                    print("=" * 60)
                    # Return URL and None for video (ComfyUI will handle None gracefully)
                    return (output_url, None)
            else:
                # Floyo platform mode: Return URL only (no download)
                # This is the recommended mode for Floyo API integration
                print("\nSTEP 6: Skipping video download (Floyo compatible mode)")
                print("-" * 60)
                print("  → Video URL returned (ready for Floyo API)")
                print("  → Use Video URL Download node if you need local file")
                print("=" * 60)
                # Return URL and None (Floyo compatible - URL only)
                return (output_url, None)
            
        except ValueError as e:
            error_msg = f"Invalid input: {str(e)}"
            print(f"\n❌ ERROR: {error_msg}")
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Error generating lipsync: {str(e)}"
            print(f"\n❌ ERROR: {error_msg}")
            raise Exception(error_msg) from e
