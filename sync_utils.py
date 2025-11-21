"""
Utility functions for Sync.so API interactions.
Handles API requests, file uploads (via URLs), and polling for completion.
Downloads files from URLs and uploads them to Sync.so API.
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
    Handles generation requests, status polling, and waiting for completion.
    """

    BASE_URL = "https://api.sync.so/v2"

    @staticmethod
    def _download_file_from_url(url, suffix=""):
        """
        Download a file from URL to a temporary file.

        Args:
            url: URL to download from
            suffix: File extension suffix for temp file (e.g., '.mp4', '.wav')

        Returns:
            str: Path to downloaded temporary file
        """
        try:
            print(f"Downloading file from URL: {url}")
            response = requests.get(url, stream=True)
            response.raise_for_status()

            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_path = temp_file.name
            temp_file.close()

            # Write content to temp file
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print(f"File downloaded successfully to: {temp_path}")
            return temp_path

        except Exception as e:
            error_msg = f"Error downloading file from URL {url}: {str(e)}"
            print(error_msg)
            raise Exception(error_msg) from e

    @staticmethod
    def _detect_mime_type(file_path):
        """
        Detect MIME type of a file based on extension.

        Args:
            file_path: Path to the file

        Returns:
            str: MIME type string
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'

    @staticmethod
    def create_generation(
        video_url,
        audio_url,
        model,
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
        
        Currently accepts URLs for video and audio as temporary solution
        until Floyo file upload logic is implemented.
        Downloads files from URLs and uploads them using multipart/form-data.

        Args:
            video_url: URL to the input video file
            audio_url: URL to the input audio file
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

        Raises:
            Exception: If API request fails
        """
        video_temp_path = None
        audio_temp_path = None
        try:
            api_key = SyncConfig().get_key()
            url = f"{SyncApiHandler.BASE_URL}/generate"

            headers = {
                "x-api-key": api_key,
            }

            # Download files from URLs to temporary files
            print(f"Downloading video from URL...")
            video_temp_path = SyncApiHandler._download_file_from_url(video_url, suffix=".mp4")
            
            print(f"Downloading audio from URL...")
            audio_temp_path = SyncApiHandler._download_file_from_url(audio_url, suffix=".wav")

            # Detect file extensions and MIME types
            video_ext = os.path.splitext(video_temp_path)[1] or '.mp4'
            audio_ext = os.path.splitext(audio_temp_path)[1] or '.wav'

            video_mime = SyncApiHandler._detect_mime_type(video_temp_path)
            audio_mime = SyncApiHandler._detect_mime_type(audio_temp_path)

            print(f"Video file: {video_temp_path} (ext: {video_ext}, mime: {video_mime})")
            print(f"Audio file: {audio_temp_path} (ext: {audio_ext}, mime: {audio_mime})")

            # Prepare multipart form data
            files = {
                'video': (f'video{video_ext}', open(video_temp_path, 'rb'), video_mime),
                'audio': (f'audio{audio_ext}', open(audio_temp_path, 'rb'), audio_mime)
            }

            # Build options JSON
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
            if occlusion_detection is not None:
                options["occlusion_detection"] = bool(occlusion_detection)
            if segment_secs is not None:
                options["segment_secs"] = float(segment_secs)
            if segment_frames is not None:
                options["segment_frames"] = int(segment_frames)

            # Prepare form data
            data = {
                'model': model
            }

            # Only add options if there are any
            if options:
                data['options'] = json.dumps(options)

            print(f"Submitting lipsync generation request to Sync.so API...")
            print(f"Model: {model}")
            print(f"Video URL: {video_url}")
            print(f"Audio URL: {audio_url}")
            if options:
                print(f"Options: {json.dumps(options, indent=2)}")

            # Submit request
            response = requests.post(url, headers=headers, files=files, data=data)

            # Close file handles
            for file_tuple in files.values():
                if hasattr(file_tuple[1], 'close'):
                    file_tuple[1].close()

            response.raise_for_status()
            result = response.json()

            print(f"Generation request submitted successfully")
            print(f"Generation ID: {result.get('id', 'N/A')}")

            return result

        except requests.exceptions.RequestException as e:
            error_msg = f"Error submitting to Sync.so API: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {json.dumps(error_detail)}"
                except:
                    error_msg += f" - {e.response.text}"
            print(error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error submitting to Sync.so API: {str(e)}"
            print(error_msg)
            raise Exception(error_msg) from e
        finally:
            # Clean up temporary files
            if video_temp_path and os.path.exists(video_temp_path):
                try:
                    os.remove(video_temp_path)
                    print(f"Cleaned up temporary video file: {video_temp_path}")
                except Exception as e:
                    print(f"Warning: Could not delete temporary video file {video_temp_path}: {str(e)}")
            if audio_temp_path and os.path.exists(audio_temp_path):
                try:
                    os.remove(audio_temp_path)
                    print(f"Cleaned up temporary audio file: {audio_temp_path}")
                except Exception as e:
                    print(f"Warning: Could not delete temporary audio file {audio_temp_path}: {str(e)}")

    @staticmethod
    def poll_status(generation_id):
        """
        Poll the status of a generation.

        Args:
            generation_id: The ID of the generation to poll

        Returns:
            dict: Generation status response

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
            print(error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error polling generation status: {str(e)}"
            print(error_msg)
            raise Exception(error_msg) from e

    @staticmethod
    def wait_for_completion(generation_id, timeout=600, poll_interval=5):
        """
        Wait for a generation to complete by polling its status.

        Args:
            generation_id: The ID of the generation to wait for
            timeout: Maximum time to wait in seconds (default: 600 = 10 minutes)
            poll_interval: Time between polls in seconds (default: 5)

        Returns:
            dict: Final generation response containing output URL

        Raises:
            Exception: If generation fails, is rejected, or times out
        """
        elapsed = 0
        print(f"Waiting for generation {generation_id} to complete...")
        print(f"Timeout: {timeout} seconds, Poll interval: {poll_interval} seconds")

        while elapsed < timeout:
            try:
                result = SyncApiHandler.poll_status(generation_id)
                status = result.get("status", "UNKNOWN")

                print(f"Generation status: {status} (elapsed: {elapsed}s)")

                if status == "COMPLETED":
                    output_url = result.get("outputUrl") or result.get("output_url") or result.get("output")
                    if output_url:
                        print(f"Generation completed successfully!")
                        print(f"Output URL: {output_url}")
                        return result
                    else:
                        raise Exception("Generation completed but no output URL found in response")

                elif status in ["FAILED", "REJECTED", "ERROR"]:
                    error_msg = result.get("error", result.get("message", "Unknown error"))
                    raise Exception(f"Generation failed with status {status}: {error_msg}")

                elif status in ["PENDING", "PROCESSING", "IN_PROGRESS"]:
                    # Continue polling
                    pass
                else:
                    print(f"Unknown status: {status}, continuing to poll...")

            except Exception as e:
                # If it's a failure status exception, re-raise it
                if "failed" in str(e).lower() or "error" in str(e).lower():
                    raise
                # Otherwise, log and continue polling (might be transient network issue)
                print(f"Error while polling (will retry): {str(e)}")

            time.sleep(poll_interval)
            elapsed += poll_interval

        raise Exception(
            f"Generation timed out after {timeout} seconds. "
            f"Last status: {SyncApiHandler.poll_status(generation_id).get('status', 'UNKNOWN')}"
        )

