"""
Video URL to Frames Node - Companion node for Sync.so Lipsync.
Converts video URLs to ComfyUI IMAGE format following Seed API pattern.
This node can be used with any API node that outputs video URLs.
"""

from typing_extensions import override
from comfy_api.latest import ComfyExtension, io

from .video_url_utils import VideoUrlUtils


class VideoUrlToFramesNode(io.ComfyNode):
    """
    Video URL to Frames Node for ComfyUI.
    
    Converts video URLs to ComfyUI IMAGE format by extracting frames.
    Follows the ComfyUI-Seed-API pattern for video URL processing.
    This node can be used with Sync.so Lipsync or any API node that outputs video URLs.
    
    Class methods
    -------------
    define_schema (io.Schema):
        Define the metadata, input, and output parameters of the node.
    execute:
        Execute the video URL to frames conversion.
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        """
        Return a schema which contains all information about the node.

        Returns:
            io.Schema: Schema definition with inputs and outputs
        """
        return io.Schema(
            node_id="VideoUrlToFrames",
            display_name="Video URL to Frames",
            category="Sync.so",
            inputs=[
                io.String.Input(
                    "video_url",
                    default="",
                    multiline=False,
                ),
                io.Int.Input(
                    "num_frames",
                    default=10,
                    min=1,
                    max=100,
                    step=1,
                    display_mode=io.NumberDisplay.number,
                    lazy=True,
                ),
                io.Float.Input(
                    "extraction_fps",
                    default=None,
                    min=0.1,
                    max=30.0,
                    step=0.1,
                    round=0.1,
                    display_mode=io.NumberDisplay.number,
                    lazy=True,
                ),
            ],
            outputs=[
                io.Image.Output("images"),
            ],
        )

    @classmethod
    def execute(
        cls,
        video_url,
        num_frames=10,
        extraction_fps=None,
    ) -> io.NodeOutput:
        """
        Execute video URL to frames conversion.

        Args:
            video_url: URL to the video file
            num_frames: Number of frames to extract (evenly distributed)
            extraction_fps: Extract frames at specific FPS (optional, overrides num_frames if provided)

        Returns:
            io.NodeOutput: Output containing extracted frames as IMAGE tensor

        Raises:
            Exception: If conversion fails
        """
        try:
            # Validate input
            if not video_url or not video_url.strip():
                raise ValueError("video_url is required and cannot be empty")

            print(f"Converting video URL to frames...")
            print(f"Video URL: {video_url}")
            print(f"Num frames: {num_frames}")
            if extraction_fps is not None:
                print(f"Extraction FPS: {extraction_fps}")

            # Extract frames from video URL
            # Use extraction_fps if provided, otherwise use num_frames
            if extraction_fps is not None:
                image_array, _ = VideoUrlUtils.video_url_to_frames(
                    video_url=video_url,
                    fps=extraction_fps,
                    keep_temp_file=False
                )
            else:
                image_array, _ = VideoUrlUtils.video_url_to_frames(
                    video_url=video_url,
                    num_frames=num_frames,
                    keep_temp_file=False
                )

            print(f"Successfully extracted {image_array.shape[0]} frames")
            print(f"Frame dimensions: {image_array.shape[1]}x{image_array.shape[2]}")
            print(f"Video URL to frames conversion completed!")

            return io.NodeOutput(image_array)

        except ValueError as e:
            error_msg = f"Invalid input: {str(e)}"
            print(error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Error converting video URL to frames: {str(e)}"
            print(error_msg)
            raise Exception(error_msg) from e

