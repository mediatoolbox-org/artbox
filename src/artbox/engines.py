"""
title: Video rendering engines for artbox render.
"""

from __future__ import annotations

import os
import re
import tempfile

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
    """
    title: Abstract base class for video rendering engines.
    """

    def __init__(self, output_path: str, fps: int = 24) -> None:
        """
        title: Initialize the engine
        parameters:
          output_path:
            type: str
            description: Full path to the final MP4 output.
          fps:
            type: int
            description: Frames per second for the output video.
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
        title: Add a slide to the rendering queue
        parameters:
          image_path:
            type: str
            description: Path to the background image (with even dimensions).
          audio_path:
            type: str | None
            description: Path to the audio file, or None if silent.
          pause_after:
            type: float
            description: Seconds of silence to append after the audio ends.
        """
        pass

    @abstractmethod
    def render(self) -> None:
        """
        title: Compose all slides and write the final video file.
        """
        pass


class MoviePyEngine(BaseVideoEngine):
    """
    title: Render videos using the moviepy library.
    """

    def __init__(self, output_path: str, fps: int = 24) -> None:
        super().__init__(output_path, fps)
        self.clips: list[ImageClip] = []

    def add_slide(
        self,
        image_path: str,
        audio_path: str | None,
        pause_after: float,
    ) -> None:
        """
        title: Create a moviepy ImageClip and attach an AudioFileClip.
        parameters:
          image_path:
            type: str
          audio_path:
            type: str | None
          pause_after:
            type: float
        """
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
        """
        title: Concatenate all moviepy clips and write to disk.
        """
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
    """
    title: Render videos directly using ffmpeg-python.
    """

    def __init__(self, output_path: str, fps: int = 24) -> None:
        super().__init__(output_path, fps)
        self.slides: list[dict[str, Any]] = []

    def add_slide(
        self,
        image_path: str,
        audio_path: str | None,
        pause_after: float,
    ) -> None:
        """
        title: Store slide paths and parameters for the ffmpeg graph.
        parameters:
          image_path:
            type: str
          audio_path:
            type: str | None
          pause_after:
            type: float
        """
        self.slides.append(
            {
                "image": image_path,
                "audio": audio_path,
                "pause": pause_after,
            }
        )

    def _render_slide_to_ts(
        self,
        idx: int,
        instr: dict[str, Any],
        tmpdir: str,
        pbar: tqdm,
    ) -> str:
        """
        title: Render a single slide to a TS file.
        parameters:
          idx:
            type: int
          instr:
            type: dict[str, Any]
          tmpdir:
            type: str
          pbar:
            type: tqdm
        returns:
          type: str
        """
        ts_output = os.path.join(tmpdir, f"slide_{idx:04d}.ts")

        v_stream = ffmpeg.input(
            instr["img"],
            format="image2",
            loop=1,
            framerate=self.fps,
        )

        if instr["audio"]:
            a_stream = (
                ffmpeg.input(instr["audio"])
                .audio.filter("apad")
                .filter("atrim", duration=instr["dur"])
                .filter("asetpts", "PTS-STARTPTS")
            )
        else:
            a_stream = ffmpeg.input(
                "anullsrc",
                f="lavfi",
                t=instr["dur"],
                r="24000",
                cl="mono",
            ).audio

        v_stream = v_stream.trim(duration=instr["dur"]).setpts("PTS-STARTPTS")

        stream = ffmpeg.output(
            v_stream,
            a_stream,
            ts_output,
            vcodec="libx264",
            acodec="aac",
            pix_fmt="yuv420p",
            r=self.fps,
            video_track_timescale=90000,
            f="mpegts",  # Force TS format for concat
        ).overwrite_output()

        process = stream.run_async(pipe_stdout=False, pipe_stderr=True)

        frame_pattern = re.compile(r"frame=\s*(\d+)")
        buffer = ""
        last_frame = 0

        while True:
            char = process.stderr.read(1)
            if not char and process.poll() is not None:
                break

            char_decoded = char.decode("utf-8", errors="replace")
            buffer += char_decoded

            if char_decoded in {"\r", "\n"}:
                match = frame_pattern.search(buffer)
                if match:
                    current_frame = int(match.group(1))
                    if current_frame > last_frame:
                        pbar.update(current_frame - last_frame)
                        last_frame = current_frame
                buffer = ""

        process.wait()
        if process.returncode != 0:
            raise ffmpeg.Error(f"ffmpeg failed on slide {idx}", b"", b"")

        # Catch up any remaining frames
        if last_frame < instr["frames"]:
            pbar.update(instr["frames"] - last_frame)

        return ts_output

    def render(self) -> None:
        """
        title: Build intermediate TS files for each slide and stream-copy them.
        """
        if not self.slides:
            raise ValueError("No slides to render.")

        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        total_frames = 0
        slide_instructions = []

        # PRECALCULATE DURATIONS
        for slide in self.slides:
            img_path = slide["image"]
            audio_path = slide["audio"]
            pause = float(slide["pause"])

            if audio_path:
                probe = ffmpeg.probe(audio_path)
                audio_dur = float(probe["format"]["duration"])
                total_dur = audio_dur + pause
            else:
                total_dur = pause if pause > 0 else 3.0

            frames_for_slide = int(total_dur * self.fps)
            total_frames += frames_for_slide

            slide_instructions.append(
                {
                    "img": img_path,
                    "audio": audio_path,
                    "dur": total_dur,
                    "frames": frames_for_slide,
                }
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            ts_files = []

            try:
                with tqdm(
                    total=total_frames, desc="FFmpeg - Building slides"
                ) as pbar:
                    # RENDER EACH SLIDE
                    for idx, instr in enumerate(slide_instructions):
                        ts_file = self._render_slide_to_ts(
                            idx, instr, tmpdir, pbar
                        )
                        ts_files.append(ts_file)

            except ffmpeg.Error:
                print("FFmpeg slide rendering failed.")
                raise

            # CONCATENATE ALL SLIDES
            concat_path = os.path.join(tmpdir, "concat.txt")
            with open(concat_path, "w") as f:
                for ts in ts_files:
                    f.write(f"file '{ts}'\n")

            print("Multiplexing complete video stream...")

            concat_cmd = ffmpeg.input(concat_path, format="concat", safe=0)
            stream = ffmpeg.output(
                concat_cmd,
                self.output_path,
                c="copy",  # Copy streams don't encode, so instant!
            ).overwrite_output()

            try:
                stream.run(capture_stdout=True, capture_stderr=True)
            except ffmpeg.Error as e:
                print("FFmpeg stream multiplexing failed.")
                if e.stderr:
                    print(e.stderr.decode("utf-8", errors="replace"))
                raise
