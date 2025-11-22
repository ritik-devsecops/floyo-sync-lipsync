"""
File utilities for handling VIDEO and AUDIO inputs from ComfyUI.
Extracts file paths from VIDEO and AUDIO objects, similar to Jacob's FileUploadUtils.

INPUT HANDLING EXPLANATION:
===========================

ComfyUI nodes can provide inputs in different formats:

1. VIDEO/AUDIO OBJECTS (from LoadVideo/LoadAudio nodes):
   - These are objects that contain file paths internally
   - May have attributes like: .file, .filename, .get_stream_source()
   - May be dictionaries with keys: 'file', 'filename', 'path'
   - FileUtils extracts the actual file path from these objects

2. FILE PATH STRINGS:
   - Direct paths like "/path/to/video.mp4"
   - Can be validated by checking if file exists

3. URL STRINGS:
   - URLs like "https://example.com/video.mp4"
   - Identified by starting with "http://" or "https://"
   - Will be downloaded later in the API handler

WORKFLOW:
=========
1. Check if input is already a string (path or URL) → return it
2. Check if input is a VIDEO/AUDIO object → extract path from attributes
3. Check if input is a dictionary → extract path from keys
4. Try string conversion as last resort
5. Validate path exists (for local files) or is URL (for remote files)
"""

import os
import tempfile
from typing import Union


class FileUtils:
    """
    Utility functions for extracting file paths from VIDEO and AUDIO inputs.
    
    Handles various ComfyUI input formats including:
    - VIDEO objects (from LoadVideo node)
    - AUDIO objects (from LoadAudio node)
    - File path strings (local files)
    - URL strings (remote files)
    
    This class ensures that regardless of input format, we can extract
    the actual file path or URL that can be used for API calls.
    """

    @staticmethod
    def get_video_path(video) -> str:
        """
        Get file path from VIDEO input.
        
        This method handles different VIDEO input formats:
        
        1. STRING (file path or URL):
           - If starts with http:// or https:// → return as URL
           - If file exists locally → return as file path
           - Otherwise → raise error
        
        2. VIDEO OBJECT (from LoadVideo node):
           - Try .get_stream_source() method
           - Try .file attribute
           - Try .filename attribute
           - Try dictionary keys: 'file', 'filename', 'path'
        
        3. DICTIONARY:
           - Check for 'file', 'filename', or 'path' keys
        
        WORKFLOW:
        =========
        Input → Check type → Extract path → Validate → Return
        
        Args:
            video: VIDEO object from ComfyUI, file path string, or URL string
                  Examples:
                  - VIDEO object from LoadVideo node
                  - "/path/to/video.mp4" (local file)
                  - "https://example.com/video.mp4" (URL)

        Returns:
            str: Path to video file or URL to video file
            
        Raises:
            Exception: If path cannot be extracted or file doesn't exist
        """
        try:
            print(f"  → Processing video input...")
            print(f"  → Input type: {type(video).__name__}")

            # ============================================================
            # CASE 1: INPUT IS ALREADY A STRING (PATH OR URL)
            # ============================================================
            if isinstance(video, str):
                print(f"  → Video is string: {video}")
                
                # Check if it's a URL
                if video.startswith(('http://', 'https://')):
                    print(f"  ✓ Detected URL: {video}")
                    return video  # Return URL as-is, will be handled in API call
                
                # Check if it's a local file path
                elif os.path.exists(video):
                    print(f"  ✓ Detected local file: {video}")
                    return video
                else:
                    raise Exception(f"Video path does not exist: {video}")

            # ============================================================
            # CASE 2: INPUT IS A VIDEO OBJECT (FROM LOADVIDEO NODE)
            # ============================================================
            # Try different methods/attributes that VIDEO objects might have
            
            # Method 1: get_stream_source() method
            if hasattr(video, 'get_stream_source'):
                path = video.get_stream_source()
                print(f"  → Found 'get_stream_source()' method: {path}")
                if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                    print(f"  ✓ Extracted path: {path}")
                    return path
                else:
                    raise Exception(f"Video stream source not found: {path}")

            # Method 2: .file attribute
            if hasattr(video, 'file'):
                path = video.file
                print(f"  → Found 'file' attribute: {path}")
                if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                    print(f"  ✓ Extracted path: {path}")
                    return path

            # Method 3: .filename attribute
            if hasattr(video, 'filename'):
                path = video.filename
                print(f"  → Found 'filename' attribute: {path}")
                if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                    print(f"  ✓ Extracted path: {path}")
                    return path

            # ============================================================
            # CASE 3: INPUT IS A DICTIONARY
            # ============================================================
            # Some VIDEO objects are represented as dictionaries
            if isinstance(video, dict):
                print(f"  → Video is dict with keys: {list(video.keys())}")
                
                # Try 'file' key
                if 'file' in video:
                    path = video['file']
                    print(f"  → Found 'file' key: {path}")
                    if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                        print(f"  ✓ Extracted path: {path}")
                        return path
                
                # Try 'filename' key
                elif 'filename' in video:
                    path = video['filename']
                    print(f"  → Found 'filename' key: {path}")
                    if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                        print(f"  ✓ Extracted path: {path}")
                        return path
                
                # Try 'path' key
                elif 'path' in video:
                    path = video['path']
                    print(f"  → Found 'path' key: {path}")
                    if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                        print(f"  ✓ Extracted path: {path}")
                        return path

            # ============================================================
            # CASE 4: TRY STRING CONVERSION AS LAST RESORT
            # ============================================================
            str_val = str(video)
            print(f"  → Trying string conversion: {str_val}")
            if os.path.exists(str_val) or str_val.startswith(('http://', 'https://')):
                print(f"  ✓ Extracted path via string conversion: {str_val}")
                return str_val

            # ============================================================
            # ERROR: COULD NOT EXTRACT PATH
            # ============================================================
            raise Exception(
                f"Could not extract video path from input. "
                f"Type: {type(video)}, Value: {video}. "
                f"Please ensure you're connecting a VIDEO output from LoadVideo node, "
                f"or providing a valid file path or URL string."
            )

        except Exception as e:
            error_msg = f"Error getting video path: {str(e)}"
            print(f"  ❌ {error_msg}")
            raise Exception(error_msg) from e

    @staticmethod
    def get_audio_path(audio) -> str:
        """
        Get file path from AUDIO input.
        
        This method handles different AUDIO input formats:
        
        1. STRING (file path or URL):
           - If starts with http:// or https:// → return as URL
           - If file exists locally → return as file path
           - Otherwise → raise error
        
        2. AUDIO OBJECT (from LoadAudio node):
           - Try .file, .filename attributes
           - Try dictionary keys: 'file', 'filename', 'path'
           - If has waveform data → save to temp file
        
        3. DICTIONARY:
           - Check for 'file', 'filename', or 'path' keys
           - If has 'waveform' and 'sample_rate' → save to temp file
        
        WORKFLOW:
        =========
        Input → Check type → Extract path or save waveform → Validate → Return
        
        Args:
            audio: AUDIO object from ComfyUI, file path string, or URL string
                   Examples:
                   - AUDIO object from LoadAudio node
                   - "/path/to/audio.wav" (local file)
                   - "https://example.com/audio.mp3" (URL)

        Returns:
            str: Path to audio file or URL to audio file
            
        Raises:
            Exception: If path cannot be extracted or file doesn't exist
        """
        try:
            print(f"  → Processing audio input...")
            print(f"  → Input type: {type(audio).__name__}")

            # ============================================================
            # CASE 1: INPUT IS ALREADY A STRING (PATH OR URL)
            # ============================================================
            if isinstance(audio, str):
                print(f"  → Audio is string: {audio}")
                
                # Check if it's a URL
                if audio.startswith(('http://', 'https://')):
                    print(f"  ✓ Detected URL: {audio}")
                    return audio  # Return URL as-is, will be handled in API call
                
                # Check if it's a local file path
                elif os.path.exists(audio):
                    print(f"  ✓ Detected local file: {audio}")
                    return audio
                else:
                    raise Exception(f"Audio path does not exist: {audio}")

            # ============================================================
            # CASE 2: INPUT IS A DICTIONARY
            # ============================================================
            # AUDIO objects are often dictionaries with waveform data or file paths
            if isinstance(audio, dict):
                print(f"  → Audio is dict with keys: {list(audio.keys())}")
                
                # Try to get file path first
                if 'file' in audio:
                    path = audio['file']
                    print(f"  → Found 'file' key: {path}")
                    if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                        print(f"  ✓ Extracted path: {path}")
                        return path
                
                elif 'filename' in audio:
                    path = audio['filename']
                    print(f"  → Found 'filename' key: {path}")
                    if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                        print(f"  ✓ Extracted path: {path}")
                        return path
                
                elif 'path' in audio:
                    path = audio['path']
                    print(f"  → Found 'path' key: {path}")
                    if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                        print(f"  ✓ Extracted path: {path}")
                        return path
                
                # If it has waveform data, save to temp file
                elif 'waveform' in audio and 'sample_rate' in audio:
                    print(f"  → Found waveform data, saving to temp file...")
                    temp_path = FileUtils.save_audio_to_temp(audio['waveform'], audio['sample_rate'])
                    print(f"  ✓ Saved waveform to temp file: {temp_path}")
                    return temp_path

            # ============================================================
            # CASE 3: INPUT IS AN AUDIO OBJECT (FROM LOADAUDIO NODE)
            # ============================================================
            # Try different attributes that AUDIO objects might have
            
            # Method 1: .file attribute
            if hasattr(audio, 'file'):
                path = audio.file
                print(f"  → Found 'file' attribute: {path}")
                if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                    print(f"  ✓ Extracted path: {path}")
                    return path

            # Method 2: .filename attribute
            if hasattr(audio, 'filename'):
                path = audio.filename
                print(f"  → Found 'filename' attribute: {path}")
                if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                    print(f"  ✓ Extracted path: {path}")
                    return path

            # Method 3: get_stream_source() method (like VIDEO)
            if hasattr(audio, 'get_stream_source'):
                path = audio.get_stream_source()
                print(f"  → Found 'get_stream_source()' method: {path}")
                if isinstance(path, str) and (os.path.exists(path) or path.startswith(('http://', 'https://'))):
                    print(f"  ✓ Extracted path: {path}")
                    return path

            # ============================================================
            # CASE 4: TRY STRING CONVERSION AS LAST RESORT
            # ============================================================
            str_val = str(audio)
            print(f"  → Trying string conversion: {str_val}")
            if os.path.exists(str_val) or str_val.startswith(('http://', 'https://')):
                print(f"  ✓ Extracted path via string conversion: {str_val}")
                return str_val

            # ============================================================
            # ERROR: COULD NOT EXTRACT PATH
            # ============================================================
            raise Exception(
                f"Could not extract audio path from input. "
                f"Type: {type(audio)}, Value: {audio}. "
                f"Please ensure you're connecting an AUDIO output from LoadAudio node, "
                f"or providing a valid file path or URL string."
            )

        except Exception as e:
            error_msg = f"Error getting audio path: {str(e)}"
            print(f"  ❌ {error_msg}")
            import traceback
            traceback.print_exc()
            raise Exception(error_msg) from e

    @staticmethod
    def save_audio_to_temp(waveform, sample_rate) -> str:
        """
        Save audio waveform to temporary file.
        
        This is used when AUDIO object contains waveform data (numpy array)
        instead of a file path. We need to save it to a file so it can be
        uploaded to the Sync.so API.
        
        WORKFLOW:
        =========
        1. Create temporary WAV file
        2. Convert waveform tensor to numpy array (if needed)
        3. Normalize format (handle different shapes and dtypes)
        4. Convert float audio (-1.0 to 1.0) to int16 (for WAV file)
        5. Write WAV file with correct sample rate
        6. Return path to temp file
        
        The temp file will be cleaned up automatically after upload.
        
        Args:
            waveform: Audio waveform tensor/array
                     Can be:
                     - numpy array
                     - PyTorch tensor (will be converted to numpy)
                     - Shape: (channels, samples) or (samples,) or (batch, channels, samples)
            sample_rate: Sample rate in Hz (e.g., 44100, 48000)

        Returns:
            str: Path to temporary WAV file
            
        Raises:
            Exception: If saving fails
        """
        try:
            import numpy as np
            import scipy.io.wavfile as wavfile

            # Create temporary WAV file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_path = temp_file.name
            temp_file.close()

            print(f"  → Saving audio waveform to temp file: {temp_path}")
            print(f"  → Sample rate: {sample_rate} Hz")
            print(f"  → Waveform shape: {waveform.shape if hasattr(waveform, 'shape') else 'unknown'}")

            # ============================================================
            # STEP 1: CONVERT TENSOR TO NUMPY (IF NEEDED)
            # ============================================================
            # If it's a PyTorch tensor, convert to numpy
            if hasattr(waveform, 'cpu'):
                print(f"  → Converting PyTorch tensor to numpy...")
                waveform = waveform.cpu().numpy()

            # ============================================================
            # STEP 2: HANDLE DIFFERENT SHAPES
            # ============================================================
            # Waveform can be:
            # - (batch, channels, samples) - remove batch dimension
            # - (channels, samples) - keep as is
            # - (samples,) - mono audio
            
            if len(waveform.shape) == 3:
                # Remove batch dimension if present
                print(f"  → Removing batch dimension...")
                waveform = waveform.squeeze(0)

            # If stereo and channels < samples, transpose
            if len(waveform.shape) == 2 and waveform.shape[0] < waveform.shape[1]:
                print(f"  → Transposing stereo audio...")
                waveform = waveform.T

            # ============================================================
            # STEP 3: CONVERT TO INT16 FORMAT (WAV FILE REQUIREMENT)
            # ============================================================
            # WAV files use int16 format (-32768 to 32767)
            # Audio data might be in float format (-1.0 to 1.0)
            
            if waveform.dtype == np.float32 or waveform.dtype == np.float64:
                # Audio is in float format, convert to int16
                print(f"  → Converting float audio to int16...")
                waveform = np.clip(waveform, -1.0, 1.0)  # Ensure in range
                waveform = (waveform * 32767).astype(np.int16)
            elif waveform.dtype != np.int16:
                # Try to convert to int16
                print(f"  → Converting to int16 format...")
                waveform = waveform.astype(np.int16)

            print(f"  → Final waveform dtype: {waveform.dtype}, shape: {waveform.shape}")

            # ============================================================
            # STEP 4: WRITE WAV FILE
            # ============================================================
            # scipy.io.wavfile.write expects:
            # - sample_rate: int
            # - data: numpy array of shape (samples,) or (samples, channels)
            wavfile.write(temp_path, int(sample_rate), waveform)

            print(f"  ✓ Audio saved successfully to {temp_path}")
            return temp_path

        except ImportError as e:
            error_msg = (
                f"Required library not found: {str(e)}. "
                f"Please install: pip install numpy scipy"
            )
            print(f"  ❌ {error_msg}")
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Error saving audio to temp file: {str(e)}"
            print(f"  ❌ {error_msg}")
            import traceback
            traceback.print_exc()
            raise Exception(error_msg) from e
