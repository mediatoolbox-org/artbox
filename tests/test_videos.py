"""Set of tests for the videos module."""

import os

from pathlib import Path

import pytest

from pytubefix.exceptions import BotDetection

from artbox.videos import Video, Youtube


TMP_PATH = Path("/tmp/artbox")
TEST_DATA_DIR = Path(__file__).parent / "data"

os.makedirs(TMP_PATH, exist_ok=True)


def test_combine_video_and_audio():
    """Test the function that combines video and audio."""
    # Example usage
    # "The Legend of Zelda Tears of the Kingdom - Official Trailer 3.mp4"
    video_path = TEST_DATA_DIR / "videos" / "pixabay-fuji.mp4"
    audio_path = TEST_DATA_DIR / "audios" / "pixabay-science.mp3"
    output_path = TMP_PATH / "video+audio.mp4"

    params = {
        "video-path": str(video_path),
        "audio-path": str(audio_path),
        "output-path": str(output_path),
    }
    video = Video(params)
    video.combine_video_and_audio()


def test_download_from_youtube():
    """Test the method that downloads videos from youtube."""
    # "https://www.youtube.com/watch?v=uHGShqcAHlQ"
    for i, url in enumerate(
        [
            "https://youtube.com/shorts/gmutDetnBLQ",
            "https://youtube.com/watch?v=6pjbaE98ftU",
        ]
    ):
        params = {"output-path": TMP_PATH, "url": url}
        youtube = Youtube(params)
        try:
            youtube.download()
        except BotDetection:
            pytest.skip("YouTube bot detection triggered, skipping in CI")


def test_remove_audio():
    """Test the function that removes audio from a video."""
    input_file = TMP_PATH / (
        "Princess Peachs Training Course in The Super Mario Bros Movie.mp4"
    )
    output_file = "peachs-no-audio.mp4"

    params = {
        "input-path": TEST_DATA_DIR / "videos" / "pixabay-fuji.mp4",
        "output-path": TMP_PATH / "video-with-no-audio.mp4",
    }

    video = Video(params)
    video.remove_audio()
