# Floyo Sync.so Lipsync - ComfyUI Custom Node

A standalone ComfyUI custom node that integrates with Sync.so API to perform video lipsync operations. Follows Seed API pattern for Floyo platform.

## Features

- **Video Lipsync**: Generate lip-synced videos with audio using Sync.so API
- **Multiple Models**: Support for lipsync-2, lipsync-1.9.0-beta, lipsync-2-pro
- **Flexible Sync Modes**: Handle mismatched video/audio durations (bounce, loop, cut_off, silence, remap)
- **Advanced Options**: Temperature control, active speaker detection, video trimming, segmentation
- **Direct Input Support**: Works with LoadVideo/LoadAudio nodes or file paths/URLs
- **Automatic Processing**: Downloads, uploads, polls, and returns complete video with audio
- **Frame Extraction**: Extract all frames from video URLs (following Seed API pattern)
- **Audio Extraction**: Automatically extracts audio from videos
- **Batch Processing**: All frames processed automatically in batch format

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

## Quick Start

### Basic Lipsync Workflow

```
LoadVideo ──┐
            ├──→ Sync.so Lipsync → output_video_url → Video URL Download → video ✅
LoadAudio ──┘
```

**Steps:**
1. Add **LoadVideo** node: Select your video file
2. Add **LoadAudio** node: Select your audio file
3. Add **Sync.so Lipsync** node:
   - Connect LoadVideo → `video` input
   - Connect LoadAudio → `audio` input
   - Select `model`: lipsync-2 (recommended)
   - Select `sync_mode`: remap (recommended)
4. Add **Video URL Download** node (Optional):
   - Connect `output_video_url` → `video_url` input
   - Video will be automatically downloaded and saved
5. **Queue Prompt**: Wait for completion

### Advanced Workflow: Upscale Lip-Synced Video

```
LoadVideo ──┐
            ├──→ Sync.so Lipsync → output_video_url
LoadAudio ──┘
                    ↓
        Video URL to Frames → [frames, audio, fps, frame_count]
                    ↓
        [Image Processing Nodes]
        (Upscale Image By, Filters, etc.)
                    ↓
        Frames to Video with Audio → final_video ✅
                    ↑
        (connect audio from Video URL to Frames)
```

**Steps:**
1. Follow basic workflow to get `output_video_url`
2. Add **Video URL to Frames** node:
   - Connect `output_video_url` → `video_url` input
   - Extracts all frames and audio automatically
3. Add **Upscale Image By** node (or any image processing):
   - Connect `frames` → `image` input
   - Set `scale_by`: 2.0 (or desired scale)
   - **Note:** Processes all frames automatically in batch
4. Add **Frames to Video with Audio** node:
   - Connect upscaled `images` → `images` input
   - Connect `audio` from Video URL to Frames → `audio` input
   - Connect `fps` from Video URL to Frames → `fps` input
   - Final video with upscaled frames and original audio

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
- `segment_secs` (FLOAT, optional): Segment video by time (seconds). Use 0 to disable
- `segment_frames` (INT, optional): Segment video by frame count. Use 0 to disable

**Outputs:**
- `output_video_url` (STRING): URL to generated lip-synced video (with audio)

**Sync Modes Explained:**
- **remap** (recommended): Adjusts video speed to match audio length
  - Example: 5s video + 11s audio → 11s output video (slower playback)
- **bounce**: Reverse playback when video < audio
- **loop**: Loop video when video < audio
- **cut_off**: Trim audio when audio > video
- **silence**: Add silence when video > audio

### Video URL to Frames Node

**Inputs:**
- `video_url` (STRING): Video URL to extract frames from

**Outputs:**
- `frames` (IMAGE): All extracted frames as IMAGE tensor batch `[batch, height, width, channels]`
- `audio` (AUDIO): Audio track from the video in ComfyUI format
- `fps` (FLOAT): FPS of the video
- `frame_count` (INT): Number of extracted frames

**Features:**
- Extracts **all frames** from video automatically
- Extracts audio automatically using FFmpeg
- Returns frames in batch format - compatible with all ComfyUI image processing nodes
- **Batch Processing:** All frames processed automatically (no splitting needed)

**Example:**
- Input: Video with 287 frames at 24 FPS
- Output: `frames` = `[287, 1920, 1080, 3]`, `audio` = audio dict, `fps` = 24.0, `frame_count` = 287

### Video URL Download Node

**Inputs:**
- `video_url` (STRING): Connect from Sync.so Lipsync `output_video_url`
- `output_path` (STRING, optional): Directory to save video
- `filename` (STRING, optional): Custom filename

**Outputs:**
- `video` (VIDEO): Downloaded video file path

### Frames to Video with Audio Node

**Inputs:**
- `images` (IMAGE): Processed frames from image processing nodes
- `fps` (FLOAT): Output video frame rate (default: 30.0)
- `audio` (AUDIO, optional): Audio file to merge (connect from Video URL to Frames)
- `video_url` (STRING, optional): Video URL to extract audio from (if audio not provided)
- `output_path` (STRING, optional): Directory to save video

**Outputs:**
- `video` (VIDEO): Final video with processed frames and audio

**Important Notes:**
- **NO upscaling/resizing:** This node does NOT perform upscaling or resizing
- Frames should be processed by other nodes (Upscale Image By, filters, etc.) before this node
- Uses input frame dimensions as-is
- Requires FFmpeg for audio extraction/merging

## Parameters Explained

### Models
- **lipsync-2**: Balanced quality and speed (recommended)
- **lipsync-1.9.0-beta**: Fastest processing
- **lipsync-2-pro**: Highest quality (may require subscription)

### Advanced Options
- **temperature** (0.0-2.0): Controls generation randomness. Lower = conservative, Higher = creative
- **active_speaker_detection**: Automatically detect active speakers in video (requires Creator tier or higher)
- **start_time/end_time**: Trim video to specific time range
- **segment_secs/segment_frames**: Process long videos in segments for better quality

## Batch Processing

### How ComfyUI IMAGE Format Works

**IMAGE type = Batch format:**
- Format: `[batch, height, width, channels]`
- Example: `[287, 1920, 1080, 3]` = 287 frames in one batch

**All ComfyUI image nodes process batches automatically:**
- Input: `[287, 1920, 1080, 3]` (287 frames)
- Upscale Image By processes all 287 frames automatically
- Output: `[287, 3840, 2160, 3]` (all 287 frames upscaled)

**No splitting needed!** Just connect nodes and use.

### Complete Batch Workflow Example

```
Video URL to Frames
  → Output: [287, 1920, 1080, 3]  (287 frames as batch)

Upscale Image By (scale_by: 2.0)
  → Input:  [287, 1920, 1080, 3]  (batch - all frames)
  → Process: Automatically upscales ALL 287 frames
  → Output: [287, 3840, 2160, 3]  (all frames upscaled)

Frames to Video with Audio
  → Input:  [287, 3840, 2160, 3]  (batch - all upscaled frames)
  → Process: Converts all frames to video
  → Output: video (with all upscaled frames)
```

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

**"Active Speaker Detection requires Creator tier"**
- Node automatically disables ASD and retries if you don't have Creator tier
- Check console for warning message

**"Prompt has no outputs"**
- Ensure Video URL Download node is connected (returns VIDEO type)
- Or connect output to other nodes that accept STRING/VIDEO

**"422 Unprocessable Entity"**
- Check that all parameters are valid
- Some parameters may not be supported by current API version

**"FFmpeg not found"**
- Install FFmpeg: `pip install imageio-ffmpeg`
- Or download from https://ffmpeg.org/download.html
- Restart ComfyUI after installation

**"Video download failed"**
- Check network connection
- Video URL may be expired or invalid
- Try downloading manually to verify URL

## Technical Details

- **API Endpoint**: `https://api.sync.so/v2/generate`
- **Polling**: Automatic, every 5 seconds, 10-minute timeout
- **File Handling**: Supports local files and URLs (auto-download)
- **Output**: Complete video file with synced audio embedded
- **Frame Extraction**: Uses OpenCV for frame extraction, FFmpeg for audio
- **Batch Processing**: All frames processed in single batch operation

## Workflow Examples

### Example 1: Simple Lipsync
```
LoadVideo → Sync.so Lipsync → Video URL Download → video ✅
LoadAudio ──┘
```

### Example 2: Upscale Lip-Synced Video
```
LoadVideo ──┐
            ├──→ Sync.so Lipsync → Video URL to Frames
LoadAudio ──┘
                    ↓
            Upscale Image By (2x)
                    ↓
            Frames to Video with Audio → final_video ✅
                    ↑
            (audio from Video URL to Frames)
```

### Example 3: Process Frames with Filters
```
Sync.so Lipsync → Video URL to Frames → [Image Filters] → Frames to Video with Audio
```

## License

See LICENSE file for details.

## Credits

- Built for Floyo platform
- Uses Sync.so API for lipsync generation
- Follows Seed API pattern for consistency
- Based on ComfyUI-Seed-API video_to_frames_node.py
