"""Video rendering engines for artbox render."""

from __future__ import annotations

import os
import re

from abc import ABC, abstractmethod
from typing import Any

import ffmpeg

from moviepy.editor import (
    AudioFileClip,
    ImageClip,
    concatenate_videoclips,
)
from tqdm import tqdm


class BaseVideoEngine(ABC):
    """Abstract base class for video rendering engines."""

    def __init__(self, output_path: str, fps: int = 24) -> None:
        """
        Initialize the engine.

        Parameters
        ----------
        output_path : str
            Full path to the final MP4 output.
        fps : int
            Frames per second for the output video.
        """
        self.output_path = output_path
        self.fps = fps

    @abstractmethod
    def add_slide(
        self,
        image_path: str,
        audio_path: str | None,
        pause_after: float,
    ) -> None:
        """
        Add a slide to the rendering queue.

        Parameters
        ----------
        image_path : str
            Path to the background image (with even dimensions).
        audio_path : str | None
            Path to the audio file, or None if silent.
        pause_after : float
            Seconds of silence to append after the audio ends.
        """
        pass

    @abstractmethod
    def render(self) -> None:
        """Compose all slides and write the final video file."""
        pass


class MoviePyEngine(BaseVideoEngine):
    """Render videos using the moviepy library."""

    def __init__(self, output_path: str, fps: int = 24) -> None:
        super().__init__(output_path, fps)
        self.clips: list[ImageClip] = []

    def add_slide(
        self,
        image_path: str,
        audio_path: str | None,
        pause_after: float,
    ) -> None:
        """Create a moviepy ImageClip and attach an AudioFileClip."""
        if audio_path:
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration + pause_after
        else:
            audio_clip = None
            duration = pause_after if pause_after > 0 else 3.0

        img_clip = ImageClip(image_path, duration=duration)

        if audio_clip:
            img_clip = img_clip.set_audio(audio_clip)

        self.clips.append(img_clip)

    def render(self) -> None:
        """Concatenate all moviepy clips and write to disk."""
        if not self.clips:
            raise ValueError("No slides to render.")

        final = concatenate_videoclips(self.clips, method="compose")
        final.write_videofile(
            self.output_path,
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
        )


class FFmpegEngine(BaseVideoEngine):
    """Render videos directly using ffmpeg-python."""

    def __init__(self, output_path: str, fps: int = 24) -> None:
        super().__init__(output_path, fps)
        self.slides: list[dict[str, Any]] = []

    def add_slide(
        self,
        image_path: str,
        audio_path: str | None,
        pause_after: float,
    ) -> None:
        """Store slide paths and parameters for the ffmpeg graph."""
        self.slides.append(
            {
                "image": image_path,
                "audio": audio_path,
                "pause": pause_after,
            }
        )

    def render(self) -> None:
        """Build the FFMPEG filter graph and execute it."""
        if not self.slides:
            raise ValueError("No slides to render.")

        streams = []
        total_frames = 0

        for slide in self.slides:
            img_path = slide["image"]
            audio_path = slide["audio"]
            pause = float(slide["pause"])

            # 1. Video stream for this slide
            # We loop the single image frame infinitely. We'll cut it to
            # the exact duration later using trim/setpts.
            v_stream = ffmpeg.input(img_path, loop=1, framerate=self.fps)

            # 2. Audio stream for this slide
            if audio_path:
                # If there's an audio file, probe it for duration

                probe = ffmpeg.probe(audio_path)
                audio_dur = float(probe["format"]["duration"])

                a_stream = ffmpeg.input(audio_path).audio

                if pause > 0:
                    # Pad the end of the audio with empty silence
                    # apad adds infinite silence, so we slice it using atrim
                    total_dur = audio_dur + pause
                    a_stream = a_stream.filter("apad").filter(
                        "atrim", duration=total_dur
                    )
            else:
                # Silent slide
                total_dur = pause if pause > 0 else 3.0
                # Generate silence using anullsrc for the duration
                a_stream = ffmpeg.input(
                    "anullsrc", f="lavfi", t=total_dur
                ).audio

            # Now trim the infinitely looping image to match the audio duration
            v_stream = v_stream.trim(duration=total_dur).setpts("PTS-STARTPTS")

            streams.append(v_stream)
            streams.append(a_stream)
            total_frames += int(total_dur * self.fps)

        # 3. Concatenate all streams
        # ffmpeg.concat takes the streams in order: v1, a1, v2, a2...
        joined = ffmpeg.concat(*streams, v=1, a=1)

        # 4. Output the final file
        # Pix_fmt yuv420p ensures compatibility with standard players
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        output = ffmpeg.output(
            joined.node[0],  # The video stream from concat
            joined.node[1],  # The audio stream from concat
            self.output_path,
            vcodec="libx264",
            acodec="aac",
            pix_fmt="yuv420p",
            r=self.fps,
        ).overwrite_output()

        try:
            process = output.run_async(pipe_stdout=True, pipe_stderr=True)
            frame_pattern = re.compile(r"frame=\s*(\d+)")

            with tqdm(
                total=total_frames, desc="FFmpeg - Building video"
            ) as pbar:
                buffer = ""
                while True:
                    # Read 1 byte at a time; ffmpeg uses \r to overwrite
                    char = process.stderr.read(1)
                    if not char and process.poll() is not None:
                        break

                    char_decoded = char.decode("utf-8", errors="replace")
                    buffer += char_decoded

                    if char_decoded in {"\r", "\n"}:
                        match = frame_pattern.search(buffer)
                        if match:
                            current_frame = int(match.group(1))
                            if current_frame > pbar.n:
                                pbar.update(current_frame - pbar.n)
                        buffer = ""

            if process.returncode != 0:
                raise ffmpeg.Error("ffmpeg failed", b"", b"")

        except ffmpeg.Error:
            print("FFmpeg rendering failed.")
            raise
