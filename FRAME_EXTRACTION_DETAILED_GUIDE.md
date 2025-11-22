# Frame Extraction & Segmentation - Complete Guide

## Part 1: Video URL to Frames Node - Frame Extraction

### Understanding num_frames vs extraction_fps

#### num_frames (Number of Frames)

**What it does:**
- Extracts a specific NUMBER of frames evenly throughout the video
- Frames are distributed evenly from start to end

**How it works:**
```
Video: 10 seconds @ 30fps = 300 total frames
num_frames: 10

Calculation:
- Step = 300 / 10 = 30 frames
- Extract frames at: 0, 30, 60, 90, 120, 150, 180, 210, 240, 270
- Result: 10 frames evenly spaced throughout 10-second video
```

**Examples:**

**Example 1: Short Video (5 seconds)**
```
Video: 5 seconds @ 30fps = 150 total frames
num_frames: 10

Result: 10 frames extracted
- 1 frame every 0.5 seconds
- Frames at: 0s, 0.5s, 1.0s, 1.5s, 2.0s, 2.5s, 3.0s, 3.5s, 4.0s, 4.5s
```

**Example 2: Long Video (60 seconds)**
```
Video: 60 seconds @ 30fps = 1800 total frames
num_frames: 30

Result: 30 frames extracted
- 1 frame every 2 seconds
- Frames evenly distributed throughout 60 seconds
```

**What if num_frames > total frames?**
```
Video: 5 seconds @ 30fps = 150 frames
num_frames: 200

Result: ALL 150 frames extracted (can't extract more than total)
```

**What if num_frames is blank/0?**
- Default value: 10 frames
- Will extract 10 frames evenly

---

#### extraction_fps (Extract at Specific FPS)

**What it does:**
- Extracts frames at a specific frame rate (FPS)
- Overrides num_frames if set (> 0)

**How it works:**
```
Video: 10 seconds @ 30fps (original video FPS)
extraction_fps: 1.0

Calculation:
- Frame interval = 30 / 1.0 = 30 frames
- Extract 1 frame every 30 frames = 1 frame per second
- Result: 10 frames (1 per second for 10 seconds)
```

**Examples:**

**Example 1: Extract at 1 FPS**
```
Video: 5 seconds @ 30fps
extraction_fps: 1.0

Result: 5 frames (1 frame per second)
- Frames at: 0s, 1s, 2s, 3s, 4s
```

**Example 2: Extract at 2 FPS**
```
Video: 11 seconds @ 30fps
extraction_fps: 2.0

Result: 22 frames (2 frames per second)
- Frames at: 0s, 0.5s, 1.0s, 1.5s, 2.0s, ... (every 0.5 seconds)
```

**Example 3: Extract at 0.5 FPS (1 frame every 2 seconds)**
```
Video: 10 seconds @ 30fps
extraction_fps: 0.5

Result: 5 frames (1 frame every 2 seconds)
- Frames at: 0s, 2s, 4s, 6s, 8s
```

**What if extraction_fps = 0.0 (default)?**
- Uses num_frames instead
- extraction_fps is disabled

**What if extraction_fps > video FPS?**
```
Video: 30fps
extraction_fps: 60.0

Result: Extracts every frame (frame_interval = 1)
- Same as extracting all frames
```

---

### When to Use Which?

#### Use num_frames When:
- ✅ You want a specific number of frames
- ✅ You don't care about exact timing
- ✅ You want evenly distributed frames
- ✅ Processing time is a concern (fewer frames = faster)

**Example:**
```
Video: 60 seconds
num_frames: 20

Use case: Quick preview, quality check
Result: 20 representative frames
```

#### Use extraction_fps When:
- ✅ You need frames at specific time intervals
- ✅ You want consistent frame spacing
- ✅ You're creating animations or time-lapse
- ✅ Frame timing matters

**Example:**
```
Video: 60 seconds
extraction_fps: 1.0

Use case: Create 1-second interval preview
Result: 60 frames (1 per second)
```

---

### Your Specific Case: 5-Second Video

**Scenario:**
- Video: 5 seconds @ 30fps = 150 total frames
- Audio: 11 seconds

**Frame Extraction Options:**

**Option 1: num_frames = 10**
```
Result: 10 frames
- 1 frame every 0.5 seconds
- Good for: Quick processing, preview
```

**Option 2: num_frames = 50**
```
Result: 50 frames
- 1 frame every 0.1 seconds
- Good for: Better quality, more frames
```

**Option 3: extraction_fps = 2.0**
```
Result: 10 frames
- 1 frame every 0.5 seconds
- Same as num_frames=10 but time-based
```

**Option 4: extraction_fps = 6.0**
```
Result: 30 frames
- 1 frame every 0.167 seconds
- Good for: Smooth processing
```

**Recommendation for 5-second video:**
- **Quick processing**: num_frames = 10-15
- **Better quality**: num_frames = 30-50
- **Time-based**: extraction_fps = 2.0-6.0

---

## Part 2: Video Length vs Audio Length - Duration Mismatch

### Your Case: Video 5 seconds, Audio 11 seconds

**Problem:** Video is shorter than audio. How to handle?

### Solution: sync_mode in Sync.so Lipsync Node

Sync.so API handles duration mismatch automatically based on `sync_mode`:

#### sync_mode Options Explained

**1. remap (Recommended - Default)**
```
Video: 5 seconds
Audio: 11 seconds

What happens:
- Video speed is adjusted to match audio length
- Video plays slower (5s → 11s)
- Speed factor: 5/11 = 0.45x (slower)
- Result: 11-second video with synced audio ✅
```

**Example:**
- Original: 5 seconds @ 30fps = 150 frames
- After remap: 11 seconds @ ~13.6fps = 150 frames (slower playback)
- Audio: 11 seconds (unchanged)
- **Final output: 11-second video with audio**

**Use when:** You want video to match audio length (recommended)

---

**2. bounce**
```
Video: 5 seconds
Audio: 11 seconds

What happens:
- Video plays forward (0-5s)
- Then plays backward (5-0s)
- Repeats until audio ends
- Result: 11-second video (5s forward + 5s backward + 1s forward)
```

**Example:**
- Video: 0s→5s (forward)
- Then: 5s→0s (backward)
- Then: 0s→1s (forward)
- **Final output: 11-second video with bouncing effect**

**Use when:** You want bouncing/reverse effect

---

**3. loop**
```
Video: 5 seconds
Audio: 11 seconds

What happens:
- Video loops 2 times (5s + 5s = 10s)
- Then plays 1 second (0-1s)
- Result: 11-second video (looped)
```

**Example:**
- Loop 1: 0s→5s
- Loop 2: 0s→5s
- Final: 0s→1s
- **Final output: 11-second video with looping**

**Use when:** You want video to loop

---

**4. cut_off**
```
Video: 5 seconds
Audio: 11 seconds

What happens:
- Audio is trimmed to match video length
- Audio cut from 11s → 5s
- Result: 5-second video with 5-second audio
```

**Example:**
- Video: 5 seconds (unchanged)
- Audio: 11s → 5s (trimmed)
- **Final output: 5-second video with trimmed audio**

**Use when:** You want to keep video length, trim audio

---

**5. silence**
```
Video: 5 seconds
Audio: 11 seconds

What happens:
- Silence added to video (5s → 11s)
- Video plays for 5s, then 6s of silence
- Result: 11-second video (5s video + 6s silence)
```

**Example:**
- Video: 0s→5s (with audio)
- Silence: 5s→11s (no video, audio continues)
- **Final output: 11-second video with silence at end**

**Use when:** You want to extend video with silence

---

### Recommended Solution for Your Case

**Video: 5 seconds, Audio: 11 seconds**

**Best Option: sync_mode = "remap"**
```
✅ Video automatically extended to 11 seconds
✅ Audio sync maintained
✅ Smooth playback (slower speed)
✅ No manual work needed
```

**Workflow:**
```
LoadVideo (5s) → Sync.so Lipsync (sync_mode: remap) → output_video_url (11s)
LoadAudio (11s) ──┘
```

**Result:** 11-second lip-synced video matching audio length!

---

## Part 3: Segmentation (segment_secs & segment_frames)

### What is Segmentation?

Segmentation breaks long videos into smaller segments for better processing quality.

**Why use it?**
- ✅ Better quality for long videos
- ✅ More accurate lipsync
- ✅ Faster processing (parallel)
- ✅ Better memory management

### segment_secs (Segment by Time)

**What it does:**
- Divides video into segments of X seconds
- Each segment processed independently
- Segments automatically stitched back together

**How it works:**
```
Video: 60 seconds
segment_secs: 10

Result:
- Segment 1: 0-10 seconds
- Segment 2: 10-20 seconds
- Segment 3: 20-30 seconds
- Segment 4: 30-40 seconds
- Segment 5: 40-50 seconds
- Segment 6: 50-60 seconds

Each segment processed separately, then stitched together
```

**Examples:**

**Example 1: Short Video (11 seconds)**
```
Video: 11 seconds
segment_secs: 5

Result:
- Segment 1: 0-5 seconds
- Segment 2: 5-10 seconds
- Segment 3: 10-11 seconds (partial)

Recommendation: Don't use segmentation for short videos
- segment_secs: 0 (disabled)
```

**Example 2: Medium Video (30 seconds)**
```
Video: 30 seconds
segment_secs: 10

Result:
- Segment 1: 0-10 seconds
- Segment 2: 10-20 seconds
- Segment 3: 20-30 seconds

Recommendation: Optional, can improve quality
- segment_secs: 10-15
```

**Example 3: Long Video (2 minutes)**
```
Video: 120 seconds
segment_secs: 10

Result:
- 12 segments of 10 seconds each
- Each processed independently
- Stitched back together

Recommendation: Use segmentation
- segment_secs: 10-20
```

**What if segment_secs = 0 (default)?**
- Segmentation disabled
- Video processed as single unit
- Good for short videos

---

### segment_frames (Segment by Frame Count)

**What it does:**
- Divides video into segments of X frames
- Alternative to segment_secs
- Use when you know frame count

**How it works:**
```
Video: 60 seconds @ 30fps = 1800 frames
segment_frames: 300

Result:
- Segment 1: Frames 0-300 (0-10 seconds)
- Segment 2: Frames 300-600 (10-20 seconds)
- Segment 3: Frames 600-900 (20-30 seconds)
- Segment 4: Frames 900-1200 (30-40 seconds)
- Segment 5: Frames 1200-1500 (40-50 seconds)
- Segment 6: Frames 1500-1800 (50-60 seconds)
```

**Examples:**

**Example 1: 5-Second Video**
```
Video: 5 seconds @ 30fps = 150 frames
segment_frames: 50

Result:
- Segment 1: 0-50 frames (0-1.67s)
- Segment 2: 50-100 frames (1.67-3.33s)
- Segment 3: 100-150 frames (3.33-5s)

Recommendation: Don't use for short videos
- segment_frames: 0 (disabled)
```

**Example 2: 11-Second Video**
```
Video: 11 seconds @ 30fps = 330 frames
segment_frames: 100

Result:
- Segment 1: 0-100 frames (0-3.33s)
- Segment 2: 100-200 frames (3.33-6.67s)
- Segment 3: 200-300 frames (6.67-10s)
- Segment 4: 300-330 frames (10-11s)

Recommendation: Optional
- segment_frames: 0 (disabled) or 100-150
```

---

### When to Use Segmentation?

#### Don't Use Segmentation When:
- ❌ Video is short (< 30 seconds)
- ❌ You want fastest processing
- ❌ Video is already high quality
- ❌ Processing is working fine

**Your case (5-11 seconds):**
```
segment_secs: 0 (disabled) ✅
segment_frames: 0 (disabled) ✅
```

#### Use Segmentation When:
- ✅ Video is long (> 60 seconds)
- ✅ You want better quality
- ✅ Processing is slow or failing
- ✅ Video has multiple scenes

**Example: 2-minute video**
```
segment_secs: 10-20 ✅
segment_frames: 0 (use segment_secs instead)
```

---

### Important Rules

1. **Use Only One:**
   - Use EITHER `segment_secs` OR `segment_frames`
   - Don't use both at the same time
   - If both set, segment_secs takes priority

2. **Set to 0 to Disable:**
   - Both default to 0 (disabled)
   - Set to 0 if you don't want segmentation

3. **API Handles Stitching:**
   - Sync.so automatically stitches segments
   - You don't need to do anything
   - Final output is complete video

---

## Part 4: Complete Examples

### Example 1: Your Case (5s Video, 11s Audio)

**Setup:**
```
Video: 5 seconds @ 30fps
Audio: 11 seconds
Goal: Match video to audio length
```

**Sync.so Lipsync Settings:**
```
sync_mode: remap ✅ (extends video to 11s)
segment_secs: 0 (disabled - video too short)
segment_frames: 0 (disabled)
```

**Result:**
- Output video: 11 seconds (video speed adjusted)
- Audio: 11 seconds (unchanged)
- ✅ Perfect match!

**Frame Extraction (if needed):**
```
Video URL to Frames:
- num_frames: 20-30 (good for 11s video)
- extraction_fps: 0.0 (use num_frames)
```

---

### Example 2: Long Video with Segmentation

**Setup:**
```
Video: 2 minutes (120 seconds) @ 30fps
Audio: 2 minutes
Goal: Best quality processing
```

**Sync.so Lipsync Settings:**
```
sync_mode: remap
segment_secs: 15 ✅ (15-second segments)
segment_frames: 0 (not used)
```

**Result:**
- 8 segments of 15 seconds each
- Each processed independently
- Stitched back together
- ✅ High quality output!

---

### Example 3: Frame Extraction for Processing

**Setup:**
```
Video: 11 seconds @ 30fps = 330 frames
Goal: Extract frames for upscaling
```

**Video URL to Frames Settings:**

**Option A: Even Distribution**
```
num_frames: 30
extraction_fps: 0.0

Result: 30 frames evenly spaced
- 1 frame every ~0.37 seconds
```

**Option B: Time-Based**
```
num_frames: 10 (ignored)
extraction_fps: 1.0

Result: 11 frames
- 1 frame per second
- Frames at: 0s, 1s, 2s, 3s, ... 10s
```

**Option C: High Quality**
```
num_frames: 110
extraction_fps: 0.0

Result: 110 frames
- 1 frame every 0.1 seconds
- Better quality for upscaling
```

---

## Summary & Quick Reference

### Frame Extraction (Video URL to Frames)

| Parameter | Use When | Example |
|-----------|----------|---------|
| `num_frames` | Want specific number of frames | 10-30 for short videos |
| `extraction_fps` | Need time-based extraction | 1.0 = 1 frame/second |
| Both 0/blank | Uses default (10 frames) | Not recommended |

### Duration Mismatch (Sync.so Lipsync)

| Video | Audio | sync_mode | Result |
|-------|-------|-----------|--------|
| 5s | 11s | remap | 11s video (slower) |
| 5s | 11s | loop | 11s video (looped) |
| 5s | 11s | cut_off | 5s video (audio trimmed) |
| 5s | 11s | silence | 11s video (with silence) |

### Segmentation (Sync.so Lipsync)

| Video Length | segment_secs | segment_frames |
|--------------|-------------|----------------|
| < 30s | 0 (disabled) | 0 (disabled) |
| 30-60s | 0 or 15 | 0 or 450-900 |
| > 60s | 10-20 | 0 (use secs) |

### Your Specific Case Recommendations

**Video: 5s, Audio: 11s**

**Sync.so Lipsync:**
```
sync_mode: remap ✅
segment_secs: 0 ✅
segment_frames: 0 ✅
```

**Frame Extraction (if needed):**
```
num_frames: 20-30
extraction_fps: 0.0
```

**Result:** Perfect 11-second synced video! 🎉

