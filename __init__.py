"""
Floyo Sync.so Lipsync - ComfyUI custom node for Sync.so lipsync API
Provides video lipsync capabilities via Sync.so API integration.
Traditional ComfyUI node structure following Seed API pattern.
"""

# Import node classes
from .nodes.sync_lipsync_node import SyncLipsyncNode
# VideoUrlToFramesNode is OPTIONAL - follows Seed API pattern for frame extraction
# If you don't need frame extraction, you can comment out these lines
from .nodes.video_url_to_frames_node_traditional import VideoUrlToFramesNode
# VideoUrlDownloadNode - Downloads video from URL and saves locally
from .nodes.video_url_download_node import VideoUrlDownloadNode
# FramesToVideoWithAudioNode - Combines processed frames with audio
from .nodes.frames_to_video_with_audio_node import FramesToVideoWithAudioNode

# Node class mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "SyncLipsyncNode": SyncLipsyncNode,
    # VideoUrlToFramesNode is OPTIONAL - uncomment/comment as needed
    "VideoUrlToFramesNode": VideoUrlToFramesNode,
    # VideoUrlDownloadNode - For downloading and saving video from URL
    "VideoUrlDownloadNode": VideoUrlDownloadNode,
    # FramesToVideoWithAudioNode - For combining processed frames with audio
    "FramesToVideoWithAudioNode": FramesToVideoWithAudioNode,
}

# Display names for ComfyUI UI
NODE_DISPLAY_NAME_MAPPINGS = {
    "SyncLipsyncNode": "Sync.so Lipsync",
    # VideoUrlToFramesNode is OPTIONAL
    "VideoUrlToFramesNode": "Video URL to Frames",
    # VideoUrlDownloadNode
    "VideoUrlDownloadNode": "Video URL Download",
    # FramesToVideoWithAudioNode
    "FramesToVideoWithAudioNode": "Frames to Video with Audio",
}

# Export for ComfyUI
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
