# Floyo Sync.so Lipsync - ComfyUI Custom Node

A standalone ComfyUI custom node that integrates with Sync.so API to perform video lipsync operations. Follows Seed API pattern for Floyo platform.

## Features

- **Video Lipsync**: Generate lip-synced videos with audio using Sync.so API
- **Multiple Models**: Support for lipsync-2, lipsync-1.9.0-beta, lipsync-2-pro
- **Flexible Sync Modes**: Handle mismatched video/audio durations (bounce, loop, cut_off, silence, remap)
- **Advanced Options**: Temperature control, active speaker detection, video trimming, segmentation
- **Direct Input Support**: Works with LoadVideo/LoadAudio nodes or file paths/URLs
- **Automatic Processing**: Downloads, uploads, polls, and returns complete video with audio
- **Video URL Download**: Companion node to download and save videos from URLs

## Installation

1. **Copy to ComfyUI custom_nodes directory:**
   ```bash
   cd ComfyUI/custom_nodes
   git clone <repo-url> floyo-sync-lipsync
   ```

2. **Install dependencies:**
   ```bash
   cd floyo-sync-lipsync
   pip install -r requirements.txt
   ```
   
   Or install as a package (using pyproject.toml):
   ```bash
   cd floyo-sync-lipsync
   pip install -e .
   ```

3. **Configure API key:**
   
   Edit `config.ini`:
   ```ini
   [API]
   SYNC_API_KEY = your_actual_api_key_here
   ```
   
   Or set environment variable:
   ```bash
   export SYNC_API_KEY=your_actual_api_key_here
   ```

4. **Restart ComfyUI**

## Usage

### Basic Workflow

```
LoadVideo ──┐
            ├──→ Sync.so Lipsync → output_video_url → Video URL Download → video ✅
LoadAudio ──┘
```

### Step-by-Step

1. **Add LoadVideo Node**: Select your video file
2. **Add LoadAudio Node**: Select your audio file
3. **Add Sync.so Lipsync Node**: 
   - Connect LoadVideo → `video` input
   - Connect LoadAudio → `audio` input
   - Select `model`: lipsync-2 (recommended)
   - Select `sync_mode`: remap (recommended)
4. **Add Video URL Download Node** (Optional):
   - Connect `output_video_url` → `video_url` input
   - Video will be automatically downloaded and saved
5. **Queue Prompt**: Wait for completion

## Node Reference

### Sync.so Lipsync Node

**Inputs:**
- `video` (VIDEO): Connect from LoadVideo node or provide file path/URL
- `audio` (AUDIO): Connect from LoadAudio node or provide file path/URL
- `model` (COMBO): lipsync-2, lipsync-1.9.0-beta, lipsync-2-pro
- `sync_mode` (COMBO): bounce, loop, cut_off, silence, remap
- `temperature` (FLOAT, optional): 0.0-2.0, default: 1.0
- `active_speaker_detection` (COMBO, optional): enable/disable
- `start_time` (FLOAT, optional): Start time in seconds for trimming
- `end_time` (FLOAT, optional): End time in seconds for trimming
- `segment_secs` (FLOAT, optional): Segment video by time (seconds). Use 0 to disable. Recommended for videos > 60 seconds
- `segment_frames` (INT, optional): Segment video by frame count. Use 0 to disable. Alternative to segment_secs

**Duration Mismatch Handling:**
- `sync_mode: remap` (recommended): Adjusts video speed to match audio length
- Example: 5s video + 11s audio → 11s output video (slower playback)
- See `FRAME_EXTRACTION_DETAILED_GUIDE.md` for complete explanation

**Outputs:**
- `output_video_url` (STRING): URL to generated lip-synced video (with audio)

### Video URL Download Node

**Inputs:**
- `video_url` (STRING): Connect from Sync.so Lipsync `output_video_url`
- `output_path` (STRING, optional): Directory to save video
- `filename` (STRING, optional): Custom filename

**Outputs:**
- `video` (VIDEO): Downloaded video file path

### Video URL to Frames Node (Optional)

**Inputs:**
- `video_url` (STRING): Video URL to extract frames from
- `num_frames` (INT): Number of frames to extract evenly (default: 10)
- `extraction_fps` (FLOAT, optional): Extract at specific FPS (default: 0.0 = use num_frames)

**Outputs:**
- `images` (IMAGE): Extracted frames as IMAGE tensor
- `video_url` (STRING): Original video URL (for audio extraction)

**Frame Extraction Guide:**
- `num_frames`: Extracts X frames evenly throughout video (e.g., 10 = 10 frames)
- `extraction_fps`: Extracts at specific rate (e.g., 1.0 = 1 frame/second)
- If `extraction_fps` = 0.0, uses `num_frames` instead
- See `FRAME_EXTRACTION_DETAILED_GUIDE.md` for complete examples

### Frames to Video with Audio Node

**Inputs:**
- `images` (IMAGE): Processed frames from image processing nodes
- `fps` (FLOAT): Output video frame rate (default: 30.0)
- `audio` (AUDIO, optional): Audio file to merge
- `video_url` (STRING, optional): Video URL to extract audio from
- `output_path` (STRING, optional): Directory to save video

**Outputs:**
- `video` (VIDEO): Final video with processed frames and audio

**Note:** Requires FFmpeg for audio extraction/merging. See AUDIO_HANDLING_WORKFLOW.md for complete workflow.

## Parameters Explained

### Models
- **lipsync-2**: Balanced quality and speed (recommended)
- **lipsync-1.9.0-beta**: Fastest processing
- **lipsync-2-pro**: Highest quality (may require subscription)

### Sync Modes
- **remap**: Adjust video speed to match audio duration (recommended)
- **bounce**: Reverse playback when video < audio
- **loop**: Loop video when video < audio
- **cut_off**: Trim audio when audio > video
- **silence**: Add silence when video > audio

### Advanced Options
- **temperature** (0.0-2.0): Controls generation randomness. Lower = conservative, Higher = creative
- **active_speaker_detection**: Automatically detect active speakers in video
- **start_time/end_time**: Trim video to specific time range
- **segment_secs/segment_frames**: Process long videos in segments for better quality (see FRAME_EXTRACTION_AND_SEGMENTATION.md)

### Frame Extraction
- **Video URL to Frames Node**: Extract frames from video URLs for image processing
- Follows Seed API pattern (standard for Floyo platform)
- See FRAME_EXTRACTION_AND_SEGMENTATION.md for detailed guide

## API Key Setup

Get your API key from [Sync.so](https://sync.so/) and set it in `config.ini`:

```ini
[API]
SYNC_API_KEY = your_api_key_here
```

## Troubleshooting

**"SYNC_API_KEY not found"**
- Check `config.ini` file exists and has correct format
- Restart ComfyUI after setting API key
- Check console logs for detailed error messages

**"Prompt has no outputs"**
- Ensure Video URL Download node is connected (returns VIDEO type)
- Or connect output to other nodes that accept STRING/VIDEO

**"422 Unprocessable Entity"**
- Check that all parameters are valid
- Some parameters may not be supported by current API version

## Technical Details

- **API Endpoint**: `https://api.sync.so/v2/generate`
- **Polling**: Automatic, every 5 seconds, 10-minute timeout
- **File Handling**: Supports local files and URLs (auto-download)
- **Output**: Complete video file with synced audio embedded

## Documentation

- `README.md` - This file (quick start)
- `QUICK_START_WORKFLOW.md` - Step-by-step workflow guide with examples
- `AUDIO_HANDLING_WORKFLOW.md` - Audio handling when processing frames
- `FRAME_EXTRACTION_AND_SEGMENTATION.md` - Frame extraction and segmentation overview
- `FRAME_EXTRACTION_DETAILED_GUIDE.md` - **Complete guide** with examples:
  - `num_frames` vs `extraction_fps` explained
  - Video/audio duration mismatch handling
  - Segmentation use cases and examples
  - Your specific case (5s video, 11s audio) solutions

## License

See LICENSE file for details.

## Credits

- Built for Floyo platform
- Uses Sync.so API for lipsync generation
- Follows Seed API pattern for consistency
