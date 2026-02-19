"""
Set of tools for video handling.

ref: https://github.com/ethand91/python-youtube/blob/master/main.py
"""

from abc import abstractmethod

import ffmpeg

from moviepy.editor import AudioFileClip, VideoFileClip
from pytubefix import YouTube as PyYouTube

from artbox.base import ArtBox


class DownloadBase(ArtBox):
    """Set of tools for handing videos."""

    @abstractmethod
    def download(self):
        """Download a video."""
        ...


def _convert_srt_to_plain_text(srt_text: str) -> str:
    """
    Convert an SRT file to plain text by removing timestamps and formatting.

    Parameters
    ----------
    srt_file_path (str): Path to the SRT file.

    Returns
    -------
    str: The extracted plain text from the SRT file.
    """
    plain_text = []
    # Skip lines that are part of SRT formatting (timestamps, etc.)
    for line in srt_text.split("\n"):
        if line.strip() and not line.strip().isdigit() and "-->" not in line:
            plain_text.append(line.strip())

    return "\n".join(plain_text)


class Youtube(DownloadBase):
    """Set of tools for handing videos."""

    def _create_youtube(self, video_url: str) -> PyYouTube:
        """Create a PyYouTube instance with appropriate auth settings."""
        use_oauth = self.args.get("use_oauth", "False") == "True"
        if use_oauth:
            return PyYouTube(
                video_url,
                use_oauth=True,
                allow_oauth_cache=True,
            )
        return PyYouTube(video_url, "WEB")

    def download(self):
        """Download a youtube video."""
        resolution = self.args.get("resolution", "")
        video_url = self.args.get("url", "")

        if not video_url:
            raise Exception("Argument `url` not given.")

        video = self._create_youtube(video_url)

        # Filter the stream by resolution if provided,
        # else get the highest resolution
        if resolution:
            video_stream = video.streams.filter(
                res=resolution, file_extension="mp4"
            ).first()
            if video_stream is None:
                raise Exception(
                    f"No video stream found with resolution {resolution}."
                )
        else:
            video_stream = video.streams.get_highest_resolution()

        try:
            video_stream.download(str(self.output_path))
            print("Video was downloaded successfully")
        except Exception as e:
            print(f"Failed to download video: {e}")

    def download_captions(self):
        """Download the English closed captions of a YouTube video."""
        video_url = self.args.get("url", "")
        lang = self.args.get("lang", "en")
        format = self.args.get("format", "text")

        yt = self._create_youtube(video_url)
        caption = yt.captions.get_by_language_code(f"a.{lang}")

        if not caption:
            print(f"No captions found for language {lang}.")
            return

        # Save the captions to a file
        cc = caption.generate_srt_captions()
        with open(str(self.output_path), "w") as f:
            if format == "text":
                cc = _convert_srt_to_plain_text(cc)
            f.write(cc)
        print("Captions downloaded successfully.")


class Video(ArtBox):
    """Set of tools for handing videos."""

    def combine_video_and_audio(self) -> None:
        """
        Combine video and audio files to create a new MP4 file.

        The result will be clipped to the time of the shorter input
        (video or audio), and the audio will fade out smoothly over the last
        5 seconds.
        """
        video_path = self.args.get("video-path", "")
        audio_path = self.args.get("audio-path", "")
        output_path = str(self.output_path)

        if not video_path:
            raise Exception("Argument `video-path` not given.")

        if not audio_path:
            raise Exception("Argument `audio-path` not given.")

        # Load the video (without audio) from the MP4 file
        video_clip = VideoFileClip(video_path)
        video_clip = video_clip.without_audio()

        # Load the audio from the MP3 file
        audio_clip = AudioFileClip(audio_path)

        # Determine the shorter duration of the two clips
        min_duration = min(video_clip.duration, audio_clip.duration)

        # Clip both the video and audio to the shorter duration
        video_clip = video_clip.subclip(0, min_duration)
        audio_clip = audio_clip.subclip(0, min_duration)

        # Apply a 5-second fade-out effect to the audio
        audio_clip = audio_clip.audio_fadeout(5)

        # Set the audio of the video clip
        final_clip = video_clip.set_audio(audio_clip)

        # Write the result to the output file
        final_clip.write_videofile(output_path, codec="libx264")

        # Close all clips
        video_clip.close()
        audio_clip.close()
        final_clip.close()

    def extract_audio(self) -> None:
        """Extract audio from an MP4 file."""
        video_path = str(self.input_path)
        output_path = str(self.output_path)

        video_clip = VideoFileClip(video_path)
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(output_path)
        audio_clip.close()
        video_clip.reader.close()

        print(f"Audio has been extracted. Output saved at '{output_path}'.")

    def get_metadata(self) -> None:
        """
        Extract metadata from an MP4 file using moviepy.

        Returns
        -------
        Metadata of the MP4 file.
        """
        file_path = str(self.input_path)

        try:
            probe = ffmpeg.probe(file_path)
            general_metadata = probe.get("format", {})
            streams_metadata = probe.get("streams", [])

            detailed_metadata = {
                "format": general_metadata.get("format_name"),
                "duration": general_metadata.get("duration"),
                "size": general_metadata.get("size"),
                "bit_rate": general_metadata.get("bit_rate"),
                "tags": general_metadata.get("tags", {}),
                "streams": [],
            }

            for stream in streams_metadata:
                stream_info = {
                    "index": stream.get("index"),
                    "type": stream.get("codec_type"),
                    "codec": stream.get("codec_name"),
                    "profile": stream.get("profile"),
                    "resolution": (
                        f"{stream.get('width')}x{stream.get('height')}"
                        if stream.get("codec_type") == "video"
                        else None
                    ),
                    "bit_rate": stream.get("bit_rate"),
                    "sample_rate": stream.get("sample_rate")
                    if stream.get("codec_type") == "audio"
                    else None,
                    "channels": stream.get("channels")
                    if stream.get("codec_type") == "audio"
                    else None,
                    "tags": stream.get("tags", {}),
                }
                detailed_metadata["streams"].append(stream_info)

        except Exception as e:
            print(f"An error occurred: {e}")
            return

        with open(self.output_path, "w") as f:
            f.write(str(detailed_metadata))
        print(detailed_metadata)

    def remove_audio(self) -> None:
        """Remove the audio from an MP4 file."""
        # Load the video
        video = VideoFileClip(str(self.input_path))

        # Set the audio track to None
        video = video.set_audio(None)

        # Write the result to a file
        video.write_videofile(str(self.output_path), codec="libx264")
