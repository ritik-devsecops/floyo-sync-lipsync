"""
Nodes package for Floyo Sync.so Lipsync extension.
Contains all node classes and their dependencies.
"""

from .sync_node import SyncLipsyncNode
from .video_url_to_frames_node import VideoUrlToFramesNode

__all__ = [
    "SyncLipsyncNode",
    "VideoUrlToFramesNode",
]

