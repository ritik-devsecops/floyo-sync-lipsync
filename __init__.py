"""
Floyo Sync.so Lipsync - ComfyUI custom node for Sync.so lipsync API
Provides video lipsync capabilities via Sync.so API integration.
"""

from typing_extensions import override
from comfy_api.latest import ComfyExtension, io

from .sync_node import SyncLipsyncNode
from .video_url_to_frames_node import VideoUrlToFramesNode


class FloyoSyncLipsyncExtension(ComfyExtension):
    """
    ComfyUI Extension for Sync.so Lipsync API integration.
    Provides nodes for video lipsync generation and video URL to frames conversion.
    """

    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        """
        Return list of node classes provided by this extension.

        Returns:
            list[type[io.ComfyNode]]: List of node classes
        """
        return [
            SyncLipsyncNode,
            VideoUrlToFramesNode,  # Companion node following Seed API pattern
        ]


async def comfy_entrypoint() -> FloyoSyncLipsyncExtension:
    """
    Entry point for ComfyUI to load this extension.
    ComfyUI calls this function to load the extension and its nodes.

    Returns:
        FloyoSyncLipsyncExtension: The extension instance with nodes
    """
    return FloyoSyncLipsyncExtension()

