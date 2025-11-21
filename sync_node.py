"""
Sync.so Lipsync Node for ComfyUI using ComfyExtension format.
Provides video lipsync capabilities via Sync.so API.
"""

from typing_extensions import override
from comfy_api.latest import ComfyExtension, io

from .sync_utils import SyncApiHandler


class SyncLipsyncNode(io.ComfyNode):
    """
    Sync.so Lipsync Node for ComfyUI.

    This node takes video and audio URLs and generates a lip-synced video
    using the Sync.so API. Currently accepts URLs as temporary solution
    until Floyo file upload logic is implemented.

    Class methods
    -------------
    define_schema (io.Schema):
        Define the metadata, input, and output parameters of the node.
    execute:
        Execute the lipsync generation with polling until completion.
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        """
        Return a schema which contains all information about the node.

        Returns:
            io.Schema: Schema definition with inputs and outputs
        """
        return io.Schema(
            node_id="SyncLipsync",
            display_name="Sync.so Lipsync",
            category="Sync.so",
            inputs=[
                io.String.Input(
                    "video_url",
                    default="",
                    multiline=False,
                ),
                io.String.Input(
                    "audio_url",
                    default="",
                    multiline=False,
                ),
                io.Combo.Input(
                    "model",
                    options=[
                        "lipsync-2",
                        "lipsync-1.9.0-beta",
                        "lipsync-2-pro",
                    ],
                ),
                io.Combo.Input(
                    "sync_mode",
                    options=[
                        "bounce",
                        "loop",
                        "cut_off",
                        "silence",
                        "remap",
                    ],
                ),
                io.Float.Input(
                    "temperature",
                    default=1.0,
                    min=0.0,
                    max=2.0,
                    step=0.1,
                    round=0.1,
                    display_mode=io.NumberDisplay.number,
                    lazy=True,
                ),
                io.Combo.Input(
                    "active_speaker_detection",
                    options=["enable", "disable"],
                ),
                io.Float.Input(
                    "start_time",
                    default=None,
                    min=0.0,
                    step=0.1,
                    round=0.1,
                    display_mode=io.NumberDisplay.number,
                    lazy=True,
                ),
                io.Float.Input(
                    "end_time",
                    default=None,
                    min=0.0,
                    step=0.1,
                    round=0.1,
                    display_mode=io.NumberDisplay.number,
                    lazy=True,
                ),
                io.Combo.Input(
                    "occlusion_detection",
                    options=["enable", "disable"],
                ),
                io.Float.Input(
                    "segment_secs",
                    default=None,
                    min=0.0,
                    step=1.0,
                    round=1.0,
                    display_mode=io.NumberDisplay.number,
                    lazy=True,
                ),
                io.Int.Input(
                    "segment_frames",
                    default=None,
                    min=0,
                    step=1,
                    display_mode=io.NumberDisplay.number,
                    lazy=True,
                ),
            ],
            outputs=[
                io.String.Output("output_video_url"),
            ],
        )

    @classmethod
    def execute(
        cls,
        video_url,
        audio_url,
        model,
        sync_mode,
        temperature=None,
        active_speaker_detection="disable",
        start_time=None,
        end_time=None,
        occlusion_detection="disable",
        segment_secs=None,
        segment_frames=None,
    ) -> io.NodeOutput:
        """
        Execute lipsync generation using Sync.so API.

        Args:
            video_url: URL to the input video file
            audio_url: URL to the input audio file
            model: Model to use for lipsync (lipsync-2, lipsync-1.9.0-beta, lipsync-2-pro)
            sync_mode: How to handle mismatched video/audio duration (bounce, loop, cut_off, silence, remap)
            temperature: Temperature parameter (0.0-2.0, optional)
            active_speaker_detection: Enable/disable active speaker detection (optional)
            start_time: Start time in seconds (optional)
            end_time: End time in seconds (optional)
            occlusion_detection: Enable/disable occlusion detection for face blocking (optional)
            segment_secs: Segment video in seconds for processing (optional)
            segment_frames: Segment video in frames for processing (optional)

        Returns:
            io.NodeOutput: Output containing the generated video URL

        Raises:
            Exception: If generation fails or times out
        """
        try:
            # Validate inputs
            if not video_url or not video_url.strip():
                raise ValueError("video_url is required and cannot be empty")
            if not audio_url or not audio_url.strip():
                raise ValueError("audio_url is required and cannot be empty")

            print(f"Starting Sync.so lipsync generation...")
            print(f"Model: {model}")
            print(f"Sync mode: {sync_mode}")
            print(f"Video URL: {video_url}")
            print(f"Audio URL: {audio_url}")
            if temperature is not None:
                print(f"Temperature: {temperature}")
            print(f"Active speaker detection: {active_speaker_detection}")
            if start_time is not None:
                print(f"Start time: {start_time}s")
            if end_time is not None:
                print(f"End time: {end_time}s")
            print(f"Occlusion detection: {occlusion_detection}")
            if segment_secs is not None:
                print(f"Segment seconds: {segment_secs}s")
            if segment_frames is not None:
                print(f"Segment frames: {segment_frames}")

            # Convert active_speaker_detection from string to boolean
            active_speaker_bool = active_speaker_detection == "enable"

            # Convert occlusion_detection from string to boolean
            occlusion_detection_bool = occlusion_detection == "enable"

            # Submit generation request
            result = SyncApiHandler.create_generation(
                video_url=video_url,
                audio_url=audio_url,
                model=model,
                sync_mode=sync_mode,
                temperature=temperature,
                active_speaker_detection=active_speaker_bool if active_speaker_detection != "disable" else None,
                start_time=start_time,
                end_time=end_time,
                occlusion_detection=occlusion_detection_bool if occlusion_detection != "disable" else None,
                segment_secs=segment_secs,
                segment_frames=segment_frames,
            )

            # Get generation ID
            generation_id = result.get("id")
            if not generation_id:
                raise Exception("No generation ID returned from API. Response: " + str(result))

            print(f"Generation created with ID: {generation_id}")
            print("Waiting for generation to complete...")

            # Wait for completion (polls until done)
            final_result = SyncApiHandler.wait_for_completion(generation_id)

            # Extract output URL
            output_url = (
                final_result.get("outputUrl")
                or final_result.get("output_url")
                or final_result.get("output")
            )
            if not output_url:
                raise Exception(
                    "Generation completed but no output URL found in response. "
                    "Response: " + str(final_result)
                )

            print(f"Generation completed successfully!")
            print(f"Output video URL: {output_url}")

            return io.NodeOutput(output_url)

        except ValueError as e:
            error_msg = f"Invalid input: {str(e)}"
            print(error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Error generating lipsync: {str(e)}"
            print(error_msg)
            raise Exception(error_msg) from e

