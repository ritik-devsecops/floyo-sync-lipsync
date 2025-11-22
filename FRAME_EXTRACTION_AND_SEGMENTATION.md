# Frame Extraction & Segmentation Guide

## Frame Extraction (Video URL to Frames Node)

### What is Frame Extraction?

Frame extraction converts a video URL into individual image frames that can be used for further image processing in ComfyUI. This follows the **Seed API pattern** that Jacob mentioned.

### Why Use Frame Extraction?

Jacob mentioned this node is "pretty good for the video_url output, and it will be used on a great number of API nodes on our platform so it will be pretty standard."

**Use Cases:**
- Process individual frames with image nodes
- Apply filters, effects, or transformations to frames
- Extract keyframes for analysis
- Create frame-by-frame animations
- Quality checks on generated videos

### How It Works

```
Sync.so Lipsync → output_video_url → Video URL to Frames → images (IMAGE batch)
```

**Process:**
1. **Input**: Video URL (from Sync.so Lipsync or any API node)
2. **Download**: Video is downloaded temporarily
3. **Extract**: Frames are extracted using OpenCV
4. **Convert**: Frames converted to ComfyUI IMAGE format
5. **Output**: Batch of images `[batch, height, width, channels]`

### Frame Extraction Options

#### Option 1: Extract N Frames (Evenly Distributed)
- **Parameter**: `num_frames` (default: 10)
- **How it works**: Extracts frames evenly throughout the video
- **Example**: 10 frames from a 60-second video = 1 frame every 6 seconds
- **Use when**: You want a specific number of representative frames

#### Option 2: Extract at Specific FPS
- **Parameter**: `extraction_fps` (default: 0.0 = disabled)
- **How it works**: Extracts frames at a specific frame rate
- **Example**: `extraction_fps = 1.0` = 1 frame per second
- **Use when**: You need frames at regular time intervals

### Example Workflow

```
LoadVideo → Sync.so Lipsync → output_video_url
                                    ↓
                          Video URL to Frames
                                    ↓
                              images (10 frames)
                                    ↓
                          [Image Processing Nodes]
                          (Filters, Effects, etc.)
```

### Technical Details

**Output Format:**
- ComfyUI IMAGE format: `[batch, height, width, channels]`
- Batch size = number of frames extracted
- Each frame: RGB format, normalized 0-1 range
- Compatible with all ComfyUI image processing nodes

**Extraction Methods:**
1. **Evenly Distributed**: `step = total_frames / num_frames`
2. **FPS-based**: `frame_interval = video_fps / extraction_fps`
3. **Specific Frames**: Can extract specific frame indices (advanced)

---

## Segmentation (Sync.so API Feature)

### What is Segmentation?

Segmentation breaks long videos into smaller segments for processing. This improves quality and processing efficiency for longer videos.

### Why Use Segmentation?

**Benefits:**
- **Better Quality**: Smaller segments = more accurate lipsync
- **Faster Processing**: Parallel processing of segments
- **Memory Efficiency**: Reduces memory usage for long videos
- **Error Recovery**: If one segment fails, others can still succeed

### How It Works

Sync.so API processes the video in segments:
1. Video is divided into segments (by time or frames)
2. Each segment is processed independently
3. Segments are stitched back together
4. Final output is a complete video

### Segmentation Options

#### Option 1: Segment by Time (Seconds)
- **Parameter**: `segment_secs` (default: 0.0 = disabled)
- **How it works**: Divides video into segments of X seconds
- **Example**: `segment_secs = 10` = 10-second segments
- **Use when**: You want time-based segmentation

**Example:**
- Video: 60 seconds
- `segment_secs = 10`
- Result: 6 segments (0-10s, 10-20s, 20-30s, etc.)

#### Option 2: Segment by Frame Count
- **Parameter**: `segment_frames` (default: 0 = disabled)
- **How it works**: Divides video into segments of X frames
- **Example**: `segment_frames = 300` = 300-frame segments
- **Use when**: You want frame-based segmentation

**Example:**
- Video: 1800 frames (60 seconds @ 30fps)
- `segment_frames = 300`
- Result: 6 segments (0-300, 300-600, 600-900, etc.)

### When to Use Segmentation

**Use Segmentation When:**
- ✅ Video is longer than 30-60 seconds
- ✅ You want better quality for long videos
- ✅ Processing is slow or failing
- ✅ Video has multiple scenes/speakers

**Don't Use Segmentation When:**
- ❌ Video is short (< 30 seconds)
- ❌ You want fastest processing
- ❌ Video is already high quality

### Recommended Settings

**Short Videos (< 30 seconds):**
```
segment_secs = 0 (disabled)
segment_frames = 0 (disabled)
```

**Medium Videos (30-60 seconds):**
```
segment_secs = 15
segment_frames = 0
```

**Long Videos (> 60 seconds):**
```
segment_secs = 10-20
segment_frames = 0
```

**Very Long Videos (> 2 minutes):**
```
segment_secs = 10
segment_frames = 0
```

### Important Notes

1. **Only Use One**: Use either `segment_secs` OR `segment_frames`, not both
2. **Set to 0 to Disable**: Both parameters default to 0 (disabled)
3. **API Handles Stitching**: Sync.so automatically stitches segments back together
4. **Quality Improvement**: Segmentation often improves quality for long videos

### Example Workflow with Segmentation

```
LoadVideo (2-minute video)
    ↓
Sync.so Lipsync
    ├─ model: lipsync-2
    ├─ sync_mode: remap
    └─ segment_secs: 10  ← Segmentation enabled
    ↓
Output: Complete 2-minute lip-synced video
(Processed in 12 segments of 10 seconds each)
```

---

## Comparison: Frame Extraction vs Segmentation

| Feature | Frame Extraction | Segmentation |
|---------|-----------------|--------------|
| **Purpose** | Extract frames for image processing | Improve quality for long videos |
| **When to Use** | Downstream image processing | Long video processing |
| **Input** | Video URL | Video file |
| **Output** | IMAGE batch | Complete video |
| **Node** | Video URL to Frames | Sync.so Lipsync (parameter) |
| **Processing** | Local (OpenCV) | API-side (Sync.so) |

### Can You Use Both?

**Yes!** You can use both in sequence:

```
Video → Sync.so Lipsync (with segmentation) → output_video_url
                                                ↓
                                    Video URL to Frames
                                                ↓
                                            images
```

This gives you:
1. Better quality (segmentation)
2. Frame-by-frame processing (frame extraction)

---

## Summary

### Frame Extraction
- **Node**: Video URL to Frames
- **Purpose**: Extract frames for image processing
- **Pattern**: Seed API standard (Jacob's recommendation)
- **Output**: IMAGE batch for ComfyUI

### Segmentation
- **Feature**: Sync.so API parameter
- **Purpose**: Improve quality for long videos
- **Options**: `segment_secs` or `segment_frames`
- **Output**: Complete processed video

Both features work together to give you the best results!

