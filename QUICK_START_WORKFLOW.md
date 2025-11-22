# Quick Start Workflow Guide

## Simple Workflow: Upscale Lip-Synced Video

Based on your screenshot, here's the simplest and recommended workflow:

### Complete Workflow (As Shown in Screenshot)

```
┌─────────────┐
│ LoadVideo   │──┐
└─────────────┘  │
                 ├──→ ┌──────────────────┐
┌─────────────┐  │    │ Sync.so Lipsync  │──→ output_video_url
│ LoadAudio   │──┘    └──────────────────┘
└─────────────┘
                      ↓
              ┌──────────────────────┐
              │ Video URL to Frames  │──→ images
              └──────────────────────┘
                      ↓
              ┌──────────────────┐
              │ Upscale Image By │──→ upscaled_images
              └──────────────────┘
                      ↓
              ┌──────────────────────────┐
              │ Frames to Video          │
              │ with Audio               │──→ final_video ✅
              └──────────────────────────┘
                      ↑
┌─────────────┐       │
│ LoadAudio   │───────┘ (connect audio here)
└─────────────┘
```

## Step-by-Step Instructions

### Step 1: Add Nodes

1. **LoadVideo** - Select your video file
2. **LoadAudio** - Select your audio file
3. **Sync.so Lipsync** - Main lipsync node
4. **Video URL to Frames** - Extract frames
5. **Upscale Image By** - Upscale frames (or any image processing)
6. **Frames to Video with Audio** - Final video creation

### Step 2: Connect Nodes

**Basic Lipsync:**
- LoadVideo → Sync.so Lipsync (video input)
- LoadAudio → Sync.so Lipsync (audio input)

**Frame Extraction:**
- Sync.so Lipsync (output_video_url) → Video URL to Frames (video_url)

**Image Processing:**
- Video URL to Frames (images) → Upscale Image By (image)
- **Upscale Settings:**
  - `upscale_method`: Choose your method (nearest-exact, lanczos, etc.)
  - `scale_by`: Set scale factor (e.g., 2.0 for 2x upscale)

**Final Video:**
- Upscale Image By (IMAGE) → Frames to Video with Audio (images)
- **LoadAudio** → Frames to Video with Audio (audio) ← **Connect here!**
- Set `fps`: 30.0 (or match original video FPS)

### Step 3: Configure Settings

**Sync.so Lipsync:**
- `model`: lipsync-2 (recommended)
- `sync_mode`: remap (recommended)
- Other settings: Use defaults or adjust as needed

**Video URL to Frames:**
- `num_frames`: 10-30 (depending on video length)
- More frames = better quality but slower processing

**Upscale Image By:**
- `upscale_method`: Choose based on your needs
- `scale_by`: 2.0 for 2x upscale, 4.0 for 4x, etc.

**Frames to Video with Audio:**
- `fps`: 30.0 (match original video FPS)
- `audio`: Connect from LoadAudio (simple!)
- `video_url`: Optional (only if audio not connected)

### Step 4: Queue and Run

Click "Queue Prompt" and wait for processing!

## Audio Connection - Simple Explanation

### ✅ Recommended: Direct Audio Connection

**Just connect LoadAudio to Frames to Video with Audio node!**

```
LoadAudio → Frames to Video with Audio (audio input)
```

**Why this is best:**
- Simple and clear
- Uses the same audio that was synced
- No extraction needed
- Works perfectly!

### Alternative: Extract from Video URL

If you don't connect audio, you can use:
```
Video URL to Frames (video_url) → Frames to Video with Audio (video_url)
```

This automatically extracts audio from the video URL.

## Image Upscaling Tips

### Choosing Upscale Method

- **nearest-exact**: Fast, good for pixel art
- **lanczos**: High quality, smooth results
- **bicubic**: Balanced quality and speed
- **ESRGAN**: Best quality (if available)

### Scale Factor

- **2.0**: 2x upscale (1080p → 4K)
- **4.0**: 4x upscale (720p → 4K)
- **1.5**: 1.5x upscale (moderate improvement)

### Frame Count

- **Short videos (< 30s)**: 10-20 frames
- **Medium videos (30-60s)**: 20-30 frames
- **Long videos (> 60s)**: 30-50 frames

More frames = better quality but slower processing.

## Common Questions

### Q: Which audio connection is better?

**A:** Direct connection from LoadAudio (as in your screenshot) is simpler and recommended!

### Q: Do I need to connect video_url?

**A:** Only if you're NOT connecting audio from LoadAudio. If you connect audio, video_url is optional.

### Q: What FPS should I use?

**A:** Match your original video FPS. Most videos are 30fps, so use 30.0.

### Q: Can I use other image processing nodes?

**A:** Yes! Any ComfyUI image processing node works:
- Filters
- Color correction
- Style transfer
- Any image manipulation

### Q: Will audio sync correctly?

**A:** Yes! As long as:
- You use the same audio that was used for lipsync
- FPS matches original video
- Frame count is appropriate for video length

## Troubleshooting

### "Video has no audio"

**Solution:**
- Make sure LoadAudio is connected to Frames to Video with Audio
- Or provide video_url to extract audio automatically

### "Audio not syncing"

**Solution:**
- Check FPS matches original video
- Ensure frame count matches video duration
- Use same audio that was used for lipsync

### "FFmpeg not found"

**Solution:**
- Only needed if using video_url for audio extraction
- Install: `brew install ffmpeg` (Mac) or `apt install ffmpeg` (Linux)
- If using direct audio connection, FFmpeg not needed!

## Summary

✅ **Your workflow is correct!**  
✅ **Direct audio connection is simplest**  
✅ **Image upscaling works perfectly**  
✅ **Audio syncs automatically**

Just follow your screenshot workflow - it's perfect! 🎉

