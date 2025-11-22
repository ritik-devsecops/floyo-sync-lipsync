# Audio Handling Workflow Guide

## Problem: Audio Management with Frame Processing

When you extract frames from a video URL and process them (upscale, filters, etc.), the original audio needs to be preserved and merged back with the processed frames.

## Solution: Complete Workflow

### Workflow Overview

```
Sync.so Lipsync → output_video_url
                    ↓
        Video URL to Frames → [images, video_url]
                    ↓
        [Image Processing Nodes]
        (Upscale, Filters, etc.)
                    ↓
        Frames to Video with Audio
        (images + video_url) → Final Video with Audio ✅
```

## Step-by-Step Workflow

### Step 1: Generate Lip-Synced Video

```
LoadVideo → Sync.so Lipsync → output_video_url
LoadAudio ──┘
```

**Output:** `output_video_url` (video with synced audio)

### Step 2: Extract Frames for Processing

```
output_video_url → Video URL to Frames
```

**Inputs:**
- `video_url`: Connect from `output_video_url`
- `num_frames`: Number of frames to extract (e.g., 30)
- `extraction_fps`: Optional FPS-based extraction

**Outputs:**
- `images`: Extracted frames (IMAGE batch)
- `video_url`: Original video URL (for audio extraction - optional)

### Step 3: Process Frames

```
images → [Image Processing Nodes]
```

**Examples:**
- **Upscale Image By** node (as shown in screenshot)
- Apply filters
- Color correction
- Style transfer
- Any ComfyUI image processing nodes

**Output:** Processed frames (still IMAGE format)

### Step 4: Merge Processed Frames with Audio

**Option A: Direct Audio Connection (Recommended - Simple)**
```
processed_images → Frames to Video with Audio
LoadAudio ──────────┘ (connect audio directly)
```

**Option B: Extract Audio from Video URL**
```
processed_images → Frames to Video with Audio
video_url ──────────┘ (audio extracted automatically)
```

**Inputs:**
- `images`: Processed frames from Step 3
- `fps`: Output video FPS (default: 30.0)
- `audio`: **Connect from LoadAudio** (recommended - simple!)
- `video_url`: Optional - use if audio not connected (from Video URL to Frames output)

**Output:**
- `video`: Final video with processed frames + audio ✅

## Complete Example Workflow (As Shown in Screenshot)

### Scenario: Upscale Lip-Synced Video

**Your Screenshot Workflow (Perfect!):**

```
1. LoadVideo → Sync.so Lipsync → output_video_url
   LoadAudio ──┘

2. output_video_url → Video URL to Frames
                      ├─ num_frames: 10
                      └─ Output: [images, video_url]

3. images → Upscale Image By
            ├─ upscale_method: nearest-exact
            ├─ scale_by: 1.00 (adjust as needed)
            └─ Output: upscaled_images

4. upscaled_images → Frames to Video with Audio
   LoadAudio ──────────┘ (direct audio connection - simple!)
                      ├─ fps: 30.0
                      └─ Output: final_video ✅
```

**Result:** Upscaled video with original synced audio!

### Why This Works

✅ **Simple Audio Connection**: Direct connection from LoadAudio (no need to extract)  
✅ **Same Audio**: Uses the same audio that was used for lipsync  
✅ **Automatic Sync**: Audio timing matches processed frames  
✅ **User-Friendly**: Clear and straightforward workflow

## Node Details

### Video URL to Frames Node

**What it does:**
- Extracts frames from video URL
- Returns frames + original video URL

**Outputs:**
- `images`: Frames for processing
- `video_url`: Original URL (contains audio)

**Why video_url is returned:**
- Audio is embedded in the original video
- Video URL is needed to extract audio later
- Keeps workflow simple and clean

### Frames to Video with Audio Node

**What it does:**
- Creates video from processed frames
- Extracts audio from original video URL
- Merges frames + audio = final video

**How it works:**
1. Converts frames to video (no audio)
2. Extracts audio from `video_url` using FFmpeg
3. Merges audio with video using FFmpeg
4. Returns final video with audio

**Requirements:**
- FFmpeg must be installed for audio extraction/merging
- If FFmpeg not available, video is saved without audio (with warning)

## Audio Connection Methods

### Method 1: Direct Audio Connection (Recommended - Simplest!)

```
Frames to Video with Audio
├─ images: processed_frames
└─ audio: LoadAudio output  ← Connect directly (as in your screenshot)
```

**Advantages:**
- ✅ **Simplest**: Just connect LoadAudio output
- ✅ **Same Audio**: Uses the same audio used for lipsync
- ✅ **No Extraction**: No need to extract audio from video
- ✅ **User-Friendly**: Clear and straightforward

**This is what you're doing in your screenshot - Perfect!**

### Method 2: Extract Audio from Video URL (Alternative)

```
Frames to Video with Audio
├─ images: processed_frames
└─ video_url: original_video_url  ← Audio extracted automatically
```

**Advantages:**
- Automatic audio extraction
- No need to keep LoadAudio connected
- Useful if you only have video URL

**When to use:** If you don't have LoadAudio connected, use `video_url` from Video URL to Frames output

## Important Notes

### Frame Count Matching

**Important:** Processed frames count should match original video duration.

**Example:**
- Original video: 10 seconds @ 30fps = 300 frames
- Extract: 30 frames (1 per second)
- Process: 30 frames
- Output: 10-second video (30 frames @ 3fps = 10 seconds)

**Or:**
- Extract all frames: 300 frames
- Process: 300 frames
- Output: 10-second video (300 frames @ 30fps = 10 seconds)

### FPS Settings

**Match original video FPS:**
- If original video is 30fps, set `fps = 30.0`
- If original video is 24fps, set `fps = 24.0`

**Check original video FPS:**
- Video URL to Frames node logs show video properties
- Or use video metadata tools

### FFmpeg Requirement

**For audio extraction/merging:**
- FFmpeg must be installed
- Install: `brew install ffmpeg` (Mac) or `apt install ffmpeg` (Linux)

**If FFmpeg not available:**
- Video is created without audio
- Warning message is shown
- You can manually merge audio later

## Troubleshooting

### "FFmpeg not found"

**Solution:**
```bash
# Mac
brew install ffmpeg

# Linux
sudo apt install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### "Audio not syncing"

**Check:**
1. FPS matches original video
2. Frame count matches video duration
3. Audio extracted correctly from video URL

### "Video has no audio"

**Possible causes:**
1. FFmpeg not installed
2. Audio extraction failed
3. Video URL has no audio

**Solution:**
- Check terminal logs for errors
- Verify FFmpeg is installed
- Try providing separate audio file

## Best Practices

1. **Preserve Original URL**: Always connect `video_url` from Video URL to Frames to Frames to Video with Audio
2. **Match FPS**: Use original video FPS in Frames to Video with Audio node
3. **Frame Count**: Extract enough frames to maintain video quality
4. **Test First**: Test with small number of frames before processing full video
5. **Keep Audio**: Always use original video URL for audio (preserves sync)

## Example Use Cases

### 1. Upscale Lip-Synced Video
```
Sync.so Lipsync → Video URL to Frames → Upscale → Frames to Video with Audio
```

### 2. Apply Filters
```
Sync.so Lipsync → Video URL to Frames → Image Filters → Frames to Video with Audio
```

### 3. Color Correction
```
Sync.so Lipsync → Video URL to Frames → Color Adjust → Frames to Video with Audio
```

### 4. Style Transfer
```
Sync.so Lipsync → Video URL to Frames → Style Transfer → Frames to Video with Audio
```

## Summary

✅ **Video URL to Frames** extracts frames + returns video URL  
✅ **Process frames** with any image processing nodes  
✅ **Frames to Video with Audio** merges processed frames + original audio  
✅ **Result:** Processed video with synced audio!

The workflow is designed to be simple and preserve audio automatically!

