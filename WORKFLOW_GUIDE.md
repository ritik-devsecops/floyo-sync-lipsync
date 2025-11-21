# Complete Workflow Guide - Sync.so Lipsync Node

## Understanding the Pattern (Based on ComfyUI-Seed-API)

Jacob mentioned that the **"Seed API video url to frames node"** is a standard pattern used across many API nodes in the Floyo platform. This document explains how this pattern works and how to use it with our Sync.so Lipsync node.

### The Pattern Explained

#### Standard API Node Workflow:

```
API Node → Video URL (STRING) → Video URL to Frames → IMAGE Tensor → Image Processing Nodes
```

**Why This Pattern?**
1. **API Nodes** generate video URLs (not local files)
2. **Video URLs** need to be converted to frames for ComfyUI image processing
3. **ComfyUI** works with IMAGE tensors, not video URLs directly
4. **Frame extraction** allows integration with existing image nodes

#### Complete Flow:

```
┌─────────────────┐
│  Sync.so API    │  Generates video at URL
│  Node           │
└────────┬────────┘
         │
         │ output_video_url (STRING)
         │ "https://api.sync.so/..."
         ▼
┌─────────────────────────────┐
│  Video URL to Frames        │  Downloads video
│  (Utility Helper)           │  Extracts frames
│                             │  Converts to IMAGE
└────────┬────────────────────┘
         │
         │ IMAGE tensor
         │ [batch, height, width, channels]
         ▼
┌─────────────────────────────┐
│  Image Processing Nodes     │  Any ComfyUI image node
│  (Save Image, Transform,    │  can now use the frames
│   Filter, etc.)             │
└─────────────────────────────┘
```

## How It Works - Step by Step

### Step 1: API Node Generates Video URL

**Sync.so Lipsync Node** generates a lip-synced video and returns:
- **Output**: `output_video_url` (STRING)
- **Format**: `"https://api.sync.so/v2/generate/{id}/output.mp4"`

```python
# In sync_node.py - execute method
output_url = final_result.get("outputUrl")  # Gets URL from API
return io.NodeOutput(output_url)  # Returns as STRING
```

### Step 2: Video URL to Frames Conversion

**Pattern from Seed API:**
1. Download video from URL
2. Extract frames using OpenCV
3. Convert frames to ComfyUI IMAGE format
4. Return IMAGE tensor

**What happens internally:**

```python
# 1. Download video from URL
video_path = download_video_from_url("https://...")

# 2. Extract frames
frames = extract_frames_from_video(video_path, num_frames=10)

# 3. Convert to ComfyUI format
# ComfyUI IMAGE format: [batch, height, width, channels]
image_array = frames_to_comfyui_image(frames)
# Result: shape [10, 720, 1280, 3] = 10 frames, 720p, RGB
```

### Step 3: Use Frames in ComfyUI Workflow

The IMAGE tensor can now be used with:
- **Save Image** node
- **Image Transform** nodes
- **Image Filter** nodes
- **Any ComfyUI image processing node**

## Complete Workflow Examples

### Example 1: Simple Workflow (Current)

```
┌──────────────────────┐
│  Sync.so Lipsync     │
│  • video_url: "..."  │
│  • audio_url: "..."  │
└──────────┬───────────┘
           │
           │ output_video_url (STRING)
           ▼
┌──────────────────────┐
│  Save Video Node     │
│  • video: <URL>      │
└──────────────────────┘
```

**This works** when Save Video node can handle URLs directly.

### Example 2: Using Video URL to Frames Pattern (Recommended)

```
┌──────────────────────┐
│  Sync.so Lipsync     │
│  • video_url: "..."  │
│  • audio_url: "..."  │
└──────────┬───────────┘
           │
           │ output_video_url (STRING)
           ▼
┌──────────────────────────────┐
│  Video URL to Frames Node    │ ← Use utility helper
│  • video_url: <from above>   │
│  • num_frames: 10            │
└──────────┬───────────────────┘
           │
           │ IMAGE tensor [10, H, W, 3]
           ▼
┌──────────────────────┐
│  Save Image Node     │
│  • image: <frames>   │
└──────────────────────┘
```

**This is the standard pattern** used in Seed API and recommended for Floyo platform.

### Example 3: Complete Processing Workflow

```
┌──────────────────────┐
│  Video Source        │ ──┐
│  (URL or Load Video) │   │
└──────────────────────┘   │
                          │
┌──────────────────────┐  │    ┌──────────────────────┐
│  Audio Source        │  │───>│  Sync.so Lipsync     │
│  (URL or Load Audio) │──┘    │                      │
└──────────────────────┘       └──────────┬───────────┘
                                          │
                                          │ output_video_url
                                          ▼
                          ┌──────────────────────────────┐
                          │  Video URL to Frames         │
                          │  • Extract 10 frames         │
                          └──────────┬───────────────────┘
                                     │
                                     │ IMAGE [10, H, W, 3]
                                     ▼
                          ┌──────────────────────────────┐
                          │  Batch Process Images        │
                          │  (Filter, Transform, etc.)   │
                          └──────────┬───────────────────┘
                                     │
                                     │ Processed IMAGE
                                     ▼
                          ┌──────────────────────────────┐
                          │  Save Images                 │
                          │  (Saves all frames)          │
                          └──────────────────────────────┘
```

## Implementation Details

### Video URL to Frames Helper

We've created `video_url_utils.py` following the Seed API pattern:

**Key Functions:**

1. **`download_video_from_url()`**
   - Downloads video from URL to temp file
   - Handles streaming for large files
   - Returns local file path

2. **`extract_frames_from_video()`**
   - Uses OpenCV to extract frames
   - Supports multiple extraction modes:
     - `num_frames`: Extract N evenly distributed frames
     - `frame_indices`: Extract specific frame numbers
     - `fps`: Extract at specific FPS rate
   - Returns list of numpy arrays

3. **`frames_to_comfyui_image()`**
   - Converts frames to ComfyUI IMAGE format
   - Normalizes to 0-1 range
   - Returns `[batch, height, width, channels]` format
   - Compatible with all ComfyUI image nodes

4. **`video_url_to_frames()`**
   - Complete workflow function
   - Combines download + extract + convert
   - Handles cleanup automatically
   - Returns ready-to-use IMAGE tensor

### How to Use in Workflow

**Option A: Create a Companion Node (Recommended)**

Create a separate "Video URL to Frames" node that can be used with any API node:

```python
class VideoUrlToFramesNode(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="VideoUrlToFrames",
            display_name="Video URL to Frames",
            category="Video",
            inputs=[
                io.String.Input("video_url"),
                io.Int.Input("num_frames", default=10, min=1, max=100),
            ],
            outputs=[
                io.Image.Output("images"),
            ],
        )
    
    @classmethod
    def execute(cls, video_url, num_frames) -> io.NodeOutput:
        from .video_url_utils import VideoUrlUtils
        
        # Use the utility helper
        image_array, _ = VideoUrlUtils.video_url_to_frames(
            video_url,
            num_frames=num_frames
        )
        
        return io.NodeOutput(image_array)
```

**Option B: Direct Integration (Advanced)**

If you want frames directly from Sync.so node, you can add an optional frame extraction output:

```python
# In sync_node.py - Add frame extraction option
outputs=[
    io.String.Output("output_video_url"),
    io.Image.Output("frames"),  # Optional frames output
]
```

But Option A is better because:
- Reusable with other API nodes
- Follows Seed API pattern
- Cleaner separation of concerns

## Best Practices

### 1. Frame Extraction Settings

**For Preview/Thumbnail:**
```python
num_frames = 1  # Just first frame
```

**For Processing:**
```python
num_frames = 10  # 10 evenly distributed frames
```

**For Full Processing:**
```python
fps = 1.0  # 1 frame per second (for 60s video = 60 frames)
```

### 2. Memory Management

- Extract only needed frames
- Clean up temp files after use
- Use batch processing for large videos

### 3. Error Handling

- Check if video URL is accessible
- Handle timeout for large downloads
- Validate frame extraction success

## Complete Example Code

### Using the Helper in Workflow

```python
from .video_url_utils import VideoUrlUtils

# In your workflow node
def process_video_url(video_url: str):
    try:
        # Extract 10 frames from video URL
        image_array, _ = VideoUrlUtils.video_url_to_frames(
            video_url=video_url,
            num_frames=10
        )
        
        # image_array is now in ComfyUI format: [10, H, W, 3]
        # Can be used with any image node
        
        return image_array
        
    except Exception as e:
        print(f"Error processing video URL: {str(e)}")
        raise
```

## Summary

**The Pattern:**
1. API Node → Video URL (STRING)
2. Video URL to Frames → IMAGE tensor
3. IMAGE tensor → Any image processing node

**Why It Works:**
- Standard pattern across Floyo API nodes
- Reusable helper utilities
- Compatible with ComfyUI image pipeline
- Clean separation of concerns

**Next Steps:**
1. Use `video_url_utils.py` helper in your workflows
2. Create companion "Video URL to Frames" node (optional)
3. Connect Sync.so Lipsync → Video URL to Frames → Image nodes

This pattern ensures **100% smooth, perfect output** as Jacob mentioned! 🎯

