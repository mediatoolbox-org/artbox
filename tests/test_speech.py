"""
title: Set of tests for the voices module.
"""

import os

from pathlib import Path

import pytest

from artbox.speech import SpeechToText, SpeechFromText

TMP_PATH = Path("/tmp/artbox")
TEST_DATA_DIR = Path(__file__).parent / "data"

os.makedirs(TMP_PATH, exist_ok=True)


@pytest.mark.parametrize("engine", ["gtts", "edge-tts"])
def test_convert_from_text(engine: str) -> None:
    """
    title: Test the conversion from text to audio.
    parameters:
      engine:
        type: str
    """
    input_path = TMP_PATH / f"totk-{engine}.txt"
    params = {
        "title": "totk",
        "input-path": str(input_path),
        "output-path": str(TMP_PATH / f"speech-{engine}.mp3"),
        "engine": engine,
    }

    with open(input_path, "w") as f:
        f.write(
            "Are you ready to join Link and Zelda in fighting "
            "off this unprecedented threat to Hyrule?"
        )

    speech = SpeechFromText(params)
    speech.convert()


@pytest.mark.parametrize(
    "engine",
    [
        "google",
        # they need special keys for the test
        # 'google_cloud',
        # 'wit',
        # 'azure',
        # 'houndify',
        # 'ibm',
        # "vosk",
        # "whisper",
        # "whisper-api",
    ],
)
def test_convert_speech_to_text(engine: str) -> None:
    """
    title: Test the conversion from text to audio.
    parameters:
      engine:
        type: str
    """
    mp3_path = TEST_DATA_DIR / "audios" / "speech.mp3"
    output_path = TMP_PATH / f"speech-{engine}.txt"

    params = {
        "input-path": str(mp3_path),
        "output-path": str(output_path),
        "engine": engine,
    }

    expected = (
        "At Open Science Labs (OSL), we are dedicated to advancing the "
        "scientific research through collaboration, innovation, and "
        "education. Our mission is to create a more inclusive, transparent, "
        "and accessible scientific community."
    ).lower()

    for char in ("(", ")", ",", "."):
        expected = expected.replace(char, "")

    speech = SpeechToText(params)
    speech.convert()

    with open(output_path, "r") as f:
        result = f.read().lower()
    assert result == expected
