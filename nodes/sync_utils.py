"""
Utility functions for Sync.so API interactions.
Handles API requests, file uploads (via URLs), and polling for completion.

API WORKFLOW EXPLANATION:
=========================

1. CREATE GENERATION (create_generation):
   - INPUT: Video and audio files (local paths or URLs)
   - PROCESS:
     * If URLs provided: Download files from URLs to temporary files
     * Upload video and audio files to Sync.so API using multipart/form-data
     * Send all parameters (model, sync_mode, temperature, etc.) as form data
   - OUTPUT: Returns generation_id (API processes asynchronously)
   
2. POLL STATUS (poll_status):
   - INPUT: generation_id
   - PROCESS: Makes GET request to check generation status
   - OUTPUT: Returns status response with current state
   
3. WAIT FOR COMPLETION (wait_for_completion):
   - INPUT: generation_id, timeout, poll_interval
   - PROCESS:
     * Polls API every poll_interval seconds (default: 5 seconds)
     * Checks status: PENDING → PROCESSING → COMPLETED
     * If FAILED/ERROR: Raises exception
     * If timeout: Raises exception
   - OUTPUT: Returns final result with outputUrl when COMPLETED

API ENDPOINTS:
==============
- POST https://api.sync.so/v2/generate
  * Upload video and audio files
  * Send parameters as form data
  * Returns: { "id": "generation_id", "status": "PENDING" }
  
- GET https://api.sync.so/v2/generate/{generation_id}
  * Check generation status
  * Returns: { "status": "PROCESSING|COMPLETED|FAILED", "outputUrl": "..." }

AUTHENTICATION:
===============
- API key is read from config.ini or SYNC_API_KEY environment variable
- Sent in header: x-api-key: <api_key>
"""

import os
import time
import tempfile
import requests
import json
import mimetypes
from .sync_config import SyncConfig


class SyncApiHandler:
    """
    Utility class for Sync.so API interactions.
    
    This class handles all communication with the Sync.so API:
    - File uploads (from local files or URLs)
    - Generation request submission
    - Status polling
    - Waiting for completion
    
    All methods are static, so you can call them directly:
    SyncApiHandler.create_generation(...)
    """

    # Base URL for Sync.so API v2
    BASE_URL = "https://api.sync.so/v2"

    @staticmethod
    def download_file_from_url(url, suffix="", output_path=None):
        """
        Download a file from URL to a local file.
        
        This is used when the user provides URLs instead of local file paths.
        Can save to a specified path or create a temporary file.
        
        WORKFLOW:
        1. Make HTTP GET request to URL
        2. Stream download to file (temp file or specified path)
        3. Return path to downloaded file
        
        Args:
            url: URL to download from (must be http:// or https://)
            suffix: File extension suffix for temp file (e.g., '.mp4', '.wav')
            output_path: Optional path to save file. If None, creates temp file.

        Returns:
            str: Path to downloaded file

        Raises:
            Exception: If download fails
        """
        try:
            print(f"  → Downloading file from URL: {url}")
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()

            # Determine output path
            if output_path is None:
                # Create temporary file with appropriate extension
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                file_path = temp_file.name
                temp_file.close()
            else:
                file_path = output_path
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)

            # Write content to file in chunks (for large files)
            print(f"  → Saving to file: {file_path}")
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size = os.path.getsize(file_path)
            print(f"  ✓ File downloaded successfully ({file_size / 1024 / 1024:.2f} MB)")
            return file_path

        except Exception as e:
            error_msg = f"Error downloading file from URL {url}: {str(e)}"
            print(f"  ❌ {error_msg}")
            raise Exception(error_msg) from e

    @staticmethod
    def _detect_mime_type(file_path):
        """
        Detect MIME type of a file based on extension.
        
        Used to set correct Content-Type when uploading files to API.
        
        Args:
            file_path: Path to the file

        Returns:
            str: MIME type string (e.g., 'video/mp4', 'audio/wav')
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'

    @staticmethod
    def create_generation(
        video_path=None,
        video_url=None,
        audio_path=None,
        audio_url=None,
        model=None,
        sync_mode=None,
        temperature=None,
        active_speaker_detection=None,
        start_time=None,
        end_time=None,
        occlusion_detection=None,
        segment_secs=None,
        segment_frames=None,
    ):
        """
        Submit lipsync generation request to Sync.so API.
        
        This is the main method that uploads files and submits the generation request.
        
        WORKFLOW:
        =========
        
        1. DETERMINE FILE SOURCES:
           - Check if video_path exists (local file) → use it
           - Else if video_url provided → download from URL to temp file
           - Same for audio
        
        2. PREPARE FILES FOR UPLOAD:
           - Open files in binary mode
           - Detect MIME types
           - Prepare multipart/form-data
        
        3. BUILD REQUEST PARAMETERS:
           - model: Required (e.g., "lipsync-2")
           - options: JSON string with all optional parameters
             * sync_mode: How to handle duration mismatch
             * temperature: Generation randomness
             * active_speaker_detection: Auto-detect speakers
             * startTime/endTime: Video trimming
             * occlusion_detection: Face blocking detection
             * segment_secs/segment_frames: Video segmentation
        
        4. UPLOAD TO API:
           - POST request to https://api.sync.so/v2/generate
           - Headers: x-api-key (from config)
           - Files: video and audio files (multipart/form-data)
           - Data: model and options (form data)
        
        5. HANDLE RESPONSE:
           - API returns immediately with generation_id
           - Status is usually "PENDING" (processing starts asynchronously)
           - Return response dict with generation_id
        
        6. CLEANUP:
           - Delete temporary files (if downloaded from URLs)
           - Keep local files (they're user's files)
        
        Args:
            video_path: Path to local video file (optional, if video_url not provided)
            video_url: URL to video file (optional, if video_path not provided)
            audio_path: Path to local audio file (optional, if audio_url not provided)
            audio_url: URL to audio file (optional, if audio_path not provided)
            model: Model to use (lipsync-2, lipsync-1.9.0-beta, lipsync-2-pro, etc.)
            sync_mode: How to handle mismatched video/audio duration (bounce, loop, cut_off, silence, remap)
            temperature: Temperature parameter (0.0-2.0)
            active_speaker_detection: Enable active speaker detection (True/False)
            start_time: Start time in seconds (optional)
            end_time: End time in seconds (optional)
            occlusion_detection: Enable occlusion detection for face blocking (True/False, optional)
            segment_secs: Segment video in seconds for processing (optional)
            segment_frames: Segment video in frames for processing (optional)

        Returns:
            dict: Generation response containing generation ID
            Example: { "id": "abc123", "status": "PENDING" }

        Raises:
            Exception: If API request fails
        """
        video_temp_path = None
        audio_temp_path = None
        video_was_downloaded = False
        audio_was_downloaded = False
        
        try:
            # ============================================================
            # STEP 1: GET API KEY FROM CONFIG
            # ============================================================
            api_key = SyncConfig().get_key()
            if not api_key:
                config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.ini")
                raise Exception(
                    f"SYNC_API_KEY not found. Please set it in config.ini or as environment variable.\n"
                    f"Config file location: {config_path}\n"
                    f"Expected format in config.ini:\n"
                    f"[API]\n"
                    f"SYNC_API_KEY = your_api_key_here"
                )
            
            url = f"{SyncApiHandler.BASE_URL}/generate"
            print(f"  → API Endpoint: {url}")

            headers = {
                "x-api-key": api_key,
            }

            # ============================================================
            # STEP 2: DETERMINE VIDEO SOURCE (LOCAL FILE OR URL)
            # ============================================================
            print("\n  [Video File Handling]")
            if video_path and os.path.exists(video_path):
                # Use local file directly
                video_temp_path = video_path
                video_was_downloaded = False
                print(f"  ✓ Using local video file: {video_path}")
            elif video_url:
                # Download from URL to temporary file
                print(f"  → Video URL provided, downloading...")
                video_temp_path = SyncApiHandler.download_file_from_url(video_url, suffix=".mp4")
                video_was_downloaded = True
            else:
                raise ValueError("Either video_path or video_url must be provided")

            # ============================================================
            # STEP 3: DETERMINE AUDIO SOURCE (LOCAL FILE OR URL)
            # ============================================================
            print("\n  [Audio File Handling]")
            if audio_path and os.path.exists(audio_path):
                # Use local file directly
                audio_temp_path = audio_path
                audio_was_downloaded = False
                print(f"  ✓ Using local audio file: {audio_path}")
            elif audio_url:
                # Download from URL to temporary file
                print(f"  → Audio URL provided, downloading...")
                audio_temp_path = SyncApiHandler.download_file_from_url(audio_url, suffix=".wav")
                audio_was_downloaded = True
            else:
                raise ValueError("Either audio_path or audio_url must be provided")

            # ============================================================
            # STEP 4: DETECT FILE EXTENSIONS AND MIME TYPES
            # ============================================================
            video_ext = os.path.splitext(video_temp_path)[1] or '.mp4'
            audio_ext = os.path.splitext(audio_temp_path)[1] or '.wav'

            video_mime = SyncApiHandler._detect_mime_type(video_temp_path)
            audio_mime = SyncApiHandler._detect_mime_type(audio_temp_path)

            print(f"\n  [File Information]")
            print(f"  Video: {os.path.basename(video_temp_path)} ({video_ext}, {video_mime})")
            print(f"  Audio: {os.path.basename(audio_temp_path)} ({audio_ext}, {audio_mime})")

            # ============================================================
            # STEP 5: BUILD OPTIONS JSON WITH ALL PARAMETERS
            # ============================================================
            # API expects options as a JSON string in form data
            options = {}
            if sync_mode:
                options["sync_mode"] = sync_mode
            if temperature is not None:
                options["temperature"] = float(temperature)
            if active_speaker_detection is not None:
                options["active_speaker_detection"] = {
                    "auto_detect": bool(active_speaker_detection)
                }
            if start_time is not None:
                options["startTime"] = float(start_time)
            if end_time is not None:
                options["endTime"] = float(end_time)
            # Note: occlusion_detection is not currently supported by Sync.so API
            # Keeping parameter in node for future compatibility, but not sending to API
            # if occlusion_detection is not None:
            #     options["occlusion_detection"] = bool(occlusion_detection)
            if segment_secs is not None:
                options["segment_secs"] = float(segment_secs)
            if segment_frames is not None:
                options["segment_frames"] = int(segment_frames)

            # ============================================================
            # STEP 6: PREPARE FORM DATA (MODEL + OPTIONS)
            # ============================================================
            data = {
                'model': model  # Required parameter
            }

            # Only add options if there are any (to keep request clean)
            if options:
                data['options'] = json.dumps(options)

            print(f"\n  [Request Parameters]")
            print(f"  Model: {model}")
            if options:
                print(f"  Options: {json.dumps(options, indent=4)}")

            # ============================================================
            # STEP 7: PREPARE MULTIPART FORM DATA FOR FILE UPLOAD
            # ============================================================
            # Open files in binary mode for upload
            # Format: ('field_name', (filename, file_handle, mime_type))
            print(f"\n  [Preparing File Upload]")
            video_file_handle = open(video_temp_path, 'rb')
            audio_file_handle = open(audio_temp_path, 'rb')
            files = {
                'video': (f'video{video_ext}', video_file_handle, video_mime),
                'audio': (f'audio{audio_ext}', audio_file_handle, audio_mime)
            }
            print(f"  ✓ Files prepared for upload")

            # ============================================================
            # STEP 8: SUBMIT POST REQUEST TO API
            # ============================================================
            # This uploads the files and submits the generation request
            # API processes asynchronously, so it returns immediately with generation_id
            print(f"\n  [Submitting to Sync.so API]")
            print(f"  → Uploading files and submitting generation request...")
            
            response = requests.post(url, headers=headers, files=files, data=data)

            # Close file handles immediately after upload
            try:
                video_file_handle.close()
                audio_file_handle.close()
            except:
                pass

            # Check for HTTP errors
            response.raise_for_status()
            result = response.json()

            print(f"  ✓ Generation request submitted successfully")
            print(f"  Generation ID: {result.get('id', 'N/A')}")
            print(f"  Status: {result.get('status', 'N/A')}")

            return result

        except requests.exceptions.RequestException as e:
            error_msg = f"Error submitting to Sync.so API: {str(e)}"
            error_detail = None
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {json.dumps(error_detail)}"
                    
                    # Check for ASD (Active Speaker Detection) tier error
                    if error_detail.get("statusCode") == 402:
                        message = error_detail.get("message", "")
                        if "ASD" in message or "Active Speaker Detection" in message:
                            print(f"\n  ⚠ WARNING: Active Speaker Detection requires Creator tier or higher.")
                            print(f"  → Automatically disabling ASD and retrying...")
                            
                            # Close current file handles if they exist
                            try:
                                if 'video_file_handle' in locals():
                                    video_file_handle.close()
                                if 'audio_file_handle' in locals():
                                    audio_file_handle.close()
                            except:
                                pass
                            
                            # Disable ASD and rebuild options
                            retry_options = options.copy()
                            if "active_speaker_detection" in retry_options:
                                del retry_options["active_speaker_detection"]
                            
                            # Rebuild data without ASD
                            retry_data = {'model': model}
                            if retry_options:
                                retry_data['options'] = json.dumps(retry_options)
                            
                            # Reopen files for retry
                            retry_video_handle = open(video_temp_path, 'rb')
                            retry_audio_handle = open(audio_temp_path, 'rb')
                            retry_files = {
                                'video': (f'video{video_ext}', retry_video_handle, video_mime),
                                'audio': (f'audio{audio_ext}', retry_audio_handle, audio_mime)
                            }
                            
                            # Retry request without ASD
                            print(f"  → Retrying request without Active Speaker Detection...")
                            retry_response = requests.post(url, headers=headers, files=retry_files, data=retry_data)
                            
                            # Close file handles after retry
                            try:
                                retry_video_handle.close()
                                retry_audio_handle.close()
                            except:
                                pass
                            
                            retry_response.raise_for_status()
                            retry_result = retry_response.json()
                            print(f"  ✓ Generation request submitted successfully (without ASD)")
                            print(f"  Generation ID: {retry_result.get('id', 'N/A')}")
                            print(f"  Status: {retry_result.get('status', 'N/A')}")
                            return retry_result
                except:
                    error_msg += f" - {e.response.text}"
            print(f"  ❌ {error_msg}")
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error submitting to Sync.so API: {str(e)}"
            print(f"  ❌ {error_msg}")
            raise Exception(error_msg) from e
        finally:
            # ============================================================
            # STEP 9: CLEANUP TEMPORARY FILES
            # ============================================================
            # Only delete files that were downloaded from URLs
            # Keep local files (they're user's files)
            if video_temp_path and video_was_downloaded and os.path.exists(video_temp_path):
                try:
                    os.remove(video_temp_path)
                    print(f"  ✓ Cleaned up temporary video file")
                except Exception as e:
                    print(f"  ⚠ Warning: Could not delete temporary video file: {str(e)}")
            if audio_temp_path and audio_was_downloaded and os.path.exists(audio_temp_path):
                try:
                    os.remove(audio_temp_path)
                    print(f"  ✓ Cleaned up temporary audio file")
                except Exception as e:
                    print(f"  ⚠ Warning: Could not delete temporary audio file: {str(e)}")

    @staticmethod
    def poll_status(generation_id):
        """
        Poll the status of a generation.
        
        This makes a GET request to check the current status of a generation.
        
        WORKFLOW:
        1. Make GET request to /generate/{generation_id}
        2. API returns current status and metadata
        3. Return response dict
        
        STATUS VALUES:
        - PENDING: Request received, waiting to start processing
        - PROCESSING: Currently processing the video
        - COMPLETED: Processing finished, outputUrl available
        - FAILED: Processing failed
        - ERROR: Error occurred
        - REJECTED: Request was rejected (e.g., invalid input)

        Args:
            generation_id: The ID of the generation to poll

        Returns:
            dict: Generation status response
            Example: {
                "id": "abc123",
                "status": "PROCESSING",
                "outputUrl": "https://..." (only when COMPLETED)
            }

        Raises:
            Exception: If API request fails
        """
        try:
            api_key = SyncConfig().get_key()
            url = f"{SyncApiHandler.BASE_URL}/generate/{generation_id}"

            headers = {
                "x-api-key": api_key,
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            error_msg = f"Error polling generation status: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {json.dumps(error_detail)}"
                except:
                    error_msg += f" - {e.response.text}"
            print(f"  ❌ {error_msg}")
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error polling generation status: {str(e)}"
            print(f"  ❌ {error_msg}")
            raise Exception(error_msg) from e

    @staticmethod
    def wait_for_completion(generation_id, timeout=600, poll_interval=5):
        """
        Wait for a generation to complete by polling its status.
        
        This method continuously polls the API until the generation is complete.
        
        WORKFLOW:
        =========
        
        1. START POLLING LOOP:
           - Poll every poll_interval seconds (default: 5 seconds)
           - Continue until status is COMPLETED, FAILED, or timeout
        
        2. CHECK STATUS:
           - PENDING/PROCESSING: Continue polling
           - COMPLETED: Extract outputUrl and return
           - FAILED/ERROR/REJECTED: Raise exception
        
        3. TIMEOUT HANDLING:
           - If elapsed time > timeout: Raise exception
           - Default timeout: 600 seconds (10 minutes)
        
        4. RETURN RESULT:
           - When COMPLETED: Return full response dict with outputUrl
           - outputUrl is the URL to the generated lip-synced video

        Args:
            generation_id: The ID of the generation to wait for
            timeout: Maximum time to wait in seconds (default: 600 = 10 minutes)
            poll_interval: Time between polls in seconds (default: 5)

        Returns:
            dict: Final generation response containing output URL
            Example: {
                "id": "abc123",
                "status": "COMPLETED",
                "outputUrl": "https://api.sync.so/v2/generate/abc123/output.mp4"
            }

        Raises:
            Exception: If generation fails, is rejected, or times out
        """
        elapsed = 0
        print(f"  → Waiting for generation {generation_id} to complete...")
        print(f"  → Timeout: {timeout} seconds, Poll interval: {poll_interval} seconds")
        print(f"  → Status updates will appear below:\n")

        while elapsed < timeout:
            try:
                # Poll the API for current status
                result = SyncApiHandler.poll_status(generation_id)
                status = result.get("status", "UNKNOWN")

                # Print status update
                elapsed_min = elapsed // 60
                elapsed_sec = elapsed % 60
                print(f"  [{elapsed_min:02d}:{elapsed_sec:02d}] Status: {status}", end="")

                # Check if completed
                if status == "COMPLETED":
                    output_url = result.get("outputUrl") or result.get("output_url") or result.get("output")
                    if output_url:
                        print(f" ✓")
                        print(f"\n  ✓ Generation completed successfully!")
                        print(f"  ✓ Output URL: {output_url}")
                        return result
                    else:
                        raise Exception("Generation completed but no output URL found in response")

                # Check if failed
                elif status in ["FAILED", "REJECTED", "ERROR"]:
                    print(f" ❌")
                    error_msg = result.get("error", result.get("message", "Unknown error"))
                    raise Exception(f"Generation failed with status {status}: {error_msg}")

                # Continue polling if still processing
                elif status in ["PENDING", "PROCESSING", "IN_PROGRESS"]:
                    print(f" (continuing...)")
                    # Continue to next iteration
                else:
                    print(f" (unknown status, continuing...)")

            except Exception as e:
                # If it's a failure status exception, re-raise it
                if "failed" in str(e).lower() or "error" in str(e).lower() or "rejected" in str(e).lower():
                    raise
                # Otherwise, log and continue polling (might be transient network issue)
                print(f"  ⚠ Error while polling (will retry): {str(e)}")

            # Wait before next poll
            time.sleep(poll_interval)
            elapsed += poll_interval

        # Timeout reached
        last_status = "UNKNOWN"
        try:
            last_result = SyncApiHandler.poll_status(generation_id)
            last_status = last_result.get('status', 'UNKNOWN')
        except:
            pass
        
        raise Exception(
            f"Generation timed out after {timeout} seconds. "
            f"Last status: {last_status}. "
            f"Generation may still be processing. You can check status manually with generation_id: {generation_id}"
        )
