# Floyo Sync.so Lipsync - ComfyUI Custom Node

A ComfyUI custom node that integrates with the Sync.so API to perform video lipsync operations. This node provides video lipsync capabilities for the Floyo platform using Sync.so's powerful API.

## Features

- **Video Lipsync**: Generate lip-synced videos with audio using Sync.so's API
- **Multiple Models**: Support for various Sync.so models (lipsync-2, lipsync-1.9.0-beta, lipsync-2-pro)
- **Flexible Sync Modes**: Handle mismatched video/audio durations with different modes:
  - `bounce`: When video < audio, bounce (reverse playback) the video
  - `loop`: When video < audio, loop the video
  - `cut_off`: When audio > video, cut off audio
  - `silence`: When video > audio, add silence to audio
  - `remap`: Slow down or speed up video to match audio duration
- **Advanced Options**: 
  - Adjustable temperature parameter (0.0-2.0)
  - Active speaker detection support
  - Occlusion detection for face blocking
  - Start/end time trimming
  - Video segmentation support (segment_secs, segment_frames) for processing long videos
- **Automatic Polling**: Waits for generation to complete automatically
- **URL-based Inputs**: Currently accepts video and audio URLs (temporary solution until Floyo file upload is implemented)
- **Error Handling**: Comprehensive error handling with user-friendly messages

## Installation

### Prerequisites

- ComfyUI installed and running
- Python 3.8 or higher
- Sync.so API key ([Get your API key](https://sync.so/))

### Installation Steps

1. **Clone or copy this repository** to your ComfyUI custom_nodes directory:
   ```bash
   cd ComfyUI/custom_nodes
   git clone <your-repo-url> floyo-sync-lipsync
   ```

   Or manually copy the `floyo-sync-lipsync` folder to your `ComfyUI/custom_nodes` directory.

2. **Install dependencies**:
   ```bash
   cd floyo-sync-lipsync
   pip install -r requirements.txt
   ```

3. **Configure your API key**:

   Edit the `config.ini` file:
   ```ini
   [API]
   SYNC_API_KEY = your_actual_api_key_here
   ```

   Or set it as an environment variable:
   ```bash
   export SYNC_API_KEY=your_actual_api_key_here
   ```

4. **Restart ComfyUI** to load the new node

## Usage

The node will appear in ComfyUI under the **"Sync.so"** category as **"Sync.so Lipsync"**.

### Inputs

**Required:**
- `video_url` (STRING): URL to the input video file
- `audio_url` (STRING): URL to the input audio file
- `model` (COMBO): Choose from available models:
  - `lipsync-2` (default, recommended)
  - `lipsync-1.9.0-beta`
  - `lipsync-2-pro`
- `sync_mode` (COMBO): How to handle mismatched video/audio duration:
  - `bounce`: When video < audio, bounce (reverse playback) the video
  - `loop`: When video < audio, loop the video
  - `cut_off`: When audio > video, cut off audio
  - `silence`: When video > audio, add silence to audio
  - `remap`: Slow down or speed up video to match audio duration

**Optional:**
- `temperature` (FLOAT): Temperature parameter (0.0 - 2.0, default: 1.0)
  - Lower values produce more conservative results
  - Higher values produce more creative results
- `active_speaker_detection` (COMBO): Enable/disable active speaker detection
  - `enable`: Automatically detect active speakers
  - `disable`: Disable active speaker detection (default)
- `start_time` (FLOAT): Start time in seconds for video trimming (optional)
- `end_time` (FLOAT): End time in seconds for video trimming (optional)
- `occlusion_detection` (COMBO): Enable/disable occlusion detection for face blocking
  - `enable`: Detect and handle occluded faces (when faces are blocked/covered)
  - `disable`: Disable occlusion detection (default)
- `segment_secs` (FLOAT): Segment video in seconds for processing (optional)
  - Useful for processing long videos in smaller chunks
  - Improves quality and reduces processing time for long videos
- `segment_frames` (INT): Segment video in frames for processing (optional)
  - Alternative to segment_secs for frame-based segmentation
  - Specify number of frames per segment

### Outputs

- `output_video_url` (STRING): URL to the generated lip-synced video

### Example Workflow

1. Connect a video URL to the `video_url` input
2. Connect an audio URL to the `audio_url` input
3. Select your preferred `model` and `sync_mode`
4. Adjust optional parameters as needed (temperature, active_speaker_detection, etc.)
5. Execute the workflow
6. The node will automatically:
   - Submit the generation request to Sync.so API
   - Poll the status until completion
  7. Output video URL can be connected to other nodes (e.g., video download nodes)

## API Key Setup

### Get Your API Key

1. Visit [Sync.so](https://sync.so/)
2. Sign up or log in to your account
3. Navigate to API settings to get your API key

### Configuration Options

You can set your API key in one of two ways:

**Option 1: config.ini file** (recommended)
```ini
[API]
SYNC_API_KEY = your_actual_api_key_here
```

**Option 2: Environment Variable**
```bash
export SYNC_API_KEY=your_actual_api_key_here
```

The node will check environment variables first, then fall back to the config.ini file.

## Troubleshooting

### Common Issues

**1. "SYNC_API_KEY not found" Error**
- Ensure your API key is set in `config.ini` or as an environment variable
- Check that the API key is not empty or a placeholder
- Restart ComfyUI after setting the API key

**2. "Generation failed" Error**
- Check that the video and audio URLs are valid and accessible
- Verify that the URLs point to supported video/audio formats
- Ensure your Sync.so API key has sufficient credits/quota
- Check the ComfyUI console for detailed error messages

**3. "Generation timed out" Error**
- The default timeout is 10 minutes (600 seconds)
- For very long videos, generation may take longer
- Check Sync.so API status page for any service issues
- Verify your internet connection is stable

**4. "Invalid input" Error**
- Ensure both `video_url` and `audio_url` are provided and non-empty
- Verify URLs are properly formatted
- Check that URLs are accessible from the ComfyUI server

**5. Node not appearing in ComfyUI**
- Ensure the folder is in the correct location: `ComfyUI/custom_nodes/floyo-sync-lipsync/`
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Restart ComfyUI completely
- Check ComfyUI console for any import errors

### Getting Help

- Check the ComfyUI console for detailed error messages
- Review Sync.so API documentation: [https://docs.sync.so/](https://docs.sync.so/)
- Ensure you're using the latest version of the node

## Technical Details

### API Endpoints Used

- **Generation**: `POST https://api.sync.so/v2/generate`
- **Status Check**: `GET https://api.sync.so/v2/generate/{generation_id}`

### Polling Behavior

- The node automatically polls the generation status every 5 seconds
- Default timeout is 10 minutes (600 seconds)
- Generation statuses: `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`

### File Format Support

- Supported video formats: MP4, MOV, AVI, and other formats supported by Sync.so API
- Supported audio formats: WAV, MP3, AAC, and other formats supported by Sync.so API

## Future Updates

This node currently accepts URLs as input (temporary solution). Future updates will include:
- Direct file upload support when Floyo file upload logic is implemented
- Additional Sync.so API features as they become available
- Enhanced error handling and retry logic

## License

See LICENSE file for details.

## Credits

- Built for the Floyo platform
- Uses Sync.so API for lipsync generation
- Based on ComfyUI custom node structure

