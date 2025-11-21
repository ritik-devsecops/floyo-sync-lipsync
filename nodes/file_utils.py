"""
File utilities for handling VIDEO and AUDIO inputs from ComfyUI.
Extracts file paths from VIDEO and AUDIO objects, similar to Jacob's FileUploadUtils.
"""

import os
import tempfile
from typing import Union


class FileUtils:
    """
    Utility functions for extracting file paths from VIDEO and AUDIO inputs.
    Handles various ComfyUI input formats including VIDEO objects, AUDIO objects, and file paths.
    """

    @staticmethod
    def get_video_path(video) -> str:
        """
        Get file path from VIDEO input.
        Supports VIDEO objects, file paths, and URL strings.

        Args:
            video: VIDEO object from ComfyUI, file path string, or URL string

        Returns:
            str: Path to video file
        """
        try:
            print(f"Processing video input...")
            print(f"Video input type: {type(video)}")

            # If it's already a string path or URL, return it
            if isinstance(video, str):
                print(f"Video is string path/URL: {video}")
                # Check if it's a URL or local path
                if video.startswith(('http://', 'https://')):
                    return video  # Return URL as-is, will be handled in API call
                elif os.path.exists(video):
                    return video  # Return local file path
                else:
                    raise Exception(f"Video path does not exist: {video}")

            # If it's a VIDEO object, try to get the file path
            # VIDEO objects in ComfyUI might have various methods/attributes
            if hasattr(video, 'get_stream_source'):
                path = video.get_stream_source()
                print(f"Found 'get_stream_source' method: {path}")
                if os.path.exists(path) or path.startswith(('http://', 'https://')):
                    return path
                else:
                    raise Exception(f"Video stream source not found: {path}")

            # If it has a file attribute
            if hasattr(video, 'file'):
                path = video.file
                print(f"Found 'file' attribute: {path}")
                if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                    return path

            # If it has a filename attribute
            if hasattr(video, 'filename'):
                path = video.filename
                print(f"Found 'filename' attribute: {path}")
                if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                    return path

            # If it's a dictionary (some VIDEO objects are dicts)
            if isinstance(video, dict):
                print(f"Video is dict with keys: {video.keys()}")
                if 'file' in video:
                    path = video['file']
                    print(f"Found 'file' key: {path}")
                    if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                        return path
                elif 'filename' in video:
                    path = video['filename']
                    print(f"Found 'filename' key: {path}")
                    if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                        return path
                elif 'path' in video:
                    path = video['path']
                    print(f"Found 'path' key: {path}")
                    if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                        return path

            # Try string conversion as last resort
            str_val = str(video)
            print(f"Converting to string: {str_val}")
            if os.path.exists(str_val) or str_val.startswith(('http://', 'https://')):
                return str_val

            raise Exception(f"Could not extract video path from input. Type: {type(video)}, Value: {video}")

        except Exception as e:
            error_msg = f"Error getting video path: {str(e)}"
            print(error_msg)
            raise Exception(error_msg) from e

    @staticmethod
    def get_audio_path(audio) -> str:
        """
        Get file path from AUDIO input.
        Supports AUDIO objects, file paths, and URL strings.

        Args:
            audio: AUDIO object from ComfyUI, file path string, or URL string

        Returns:
            str: Path to audio file
        """
        try:
            print(f"Processing audio input...")
            print(f"Audio input type: {type(audio)}")

            # If it's already a string path or URL, return it
            if isinstance(audio, str):
                print(f"Audio is string path/URL: {audio}")
                # Check if it's a URL or local path
                if audio.startswith(('http://', 'https://')):
                    return audio  # Return URL as-is, will be handled in API call
                elif os.path.exists(audio):
                    return audio  # Return local file path
                else:
                    raise Exception(f"Audio path does not exist: {audio}")

            # If it's an AUDIO object, try to get the file path
            # AUDIO objects in ComfyUI are typically dictionaries with 'waveform' and 'sample_rate'
            # or have a file path attribute
            if isinstance(audio, dict):
                print(f"Audio is dict with keys: {audio.keys()}")
                # Check for file path first
                if 'file' in audio:
                    path = audio['file']
                    print(f"Found 'file' key: {path}")
                    if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                        return path
                elif 'filename' in audio:
                    path = audio['filename']
                    print(f"Found 'filename' key: {path}")
                    if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                        return path
                elif 'path' in audio:
                    path = audio['path']
                    print(f"Found 'path' key: {path}")
                    if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                        return path
                # If it has waveform data, we need to save it to a temp file
                elif 'waveform' in audio and 'sample_rate' in audio:
                    print(f"Found waveform data, saving to temp file...")
                    return FileUtils.save_audio_to_temp(audio['waveform'], audio['sample_rate'])

            # If it has a file attribute
            if hasattr(audio, 'file'):
                path = audio.file
                print(f"Found 'file' attribute: {path}")
                if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                    return path

            if hasattr(audio, 'filename'):
                path = audio.filename
                print(f"Found 'filename' attribute: {path}")
                if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                    return path

            # If it has get_stream_source like VIDEO
            if hasattr(audio, 'get_stream_source'):
                path = audio.get_stream_source()
                print(f"Found 'get_stream_source' method: {path}")
                if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                    return path

            # Try string conversion as last resort
            str_val = str(audio)
            print(f"Converting to string: {str_val}")
            if os.path.exists(str_val) or str_val.startswith(('http://', 'https://')):
                return str_val

            raise Exception(f"Could not extract audio path from input. Type: {type(audio)}, Value: {audio}")

        except Exception as e:
            error_msg = f"Error getting audio path: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            raise Exception(error_msg) from e

    @staticmethod
    def save_audio_to_temp(waveform, sample_rate) -> str:
        """
        Save audio waveform to temporary file.
        Used when AUDIO object contains waveform data instead of file path.

        Args:
            waveform: Audio waveform tensor
            sample_rate: Sample rate in Hz

        Returns:
            str: Path to temporary audio file
        """
        try:
            import numpy as np
            import scipy.io.wavfile as wavfile

            # Create temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_path = temp_file.name
            temp_file.close()

            print(f"Saving audio to temp file: {temp_path}")
            print(f"Sample rate: {sample_rate} Hz")
            print(f"Waveform shape: {waveform.shape if hasattr(waveform, 'shape') else 'unknown'}")

            # Convert tensor to numpy if needed
            if hasattr(waveform, 'cpu'):
                waveform = waveform.cpu().numpy()

            # Ensure we have the right shape (channels, samples) or (samples,)
            if len(waveform.shape) == 3:
                # Remove batch dimension if present
                waveform = waveform.squeeze(0)

            # If stereo, transpose to (samples, channels)
            if len(waveform.shape) == 2 and waveform.shape[0] < waveform.shape[1]:
                waveform = waveform.T

            # Ensure proper format for wav file
            if waveform.dtype == np.float32 or waveform.dtype == np.float64:
                # Audio is in float format (-1.0 to 1.0), convert to int16
                waveform = np.clip(waveform, -1.0, 1.0)
                waveform = (waveform * 32767).astype(np.int16)
            elif waveform.dtype != np.int16:
                # Try to convert to int16
                waveform = waveform.astype(np.int16)

            print(f"Final waveform dtype: {waveform.dtype}, shape: {waveform.shape}")

            # Write wav file with proper sample rate
            wavfile.write(temp_path, int(sample_rate), waveform)

            print(f"Audio saved successfully to {temp_path}")
            return temp_path

        except Exception as e:
            error_msg = f"Error saving audio to temp file: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            raise Exception(error_msg) from e

