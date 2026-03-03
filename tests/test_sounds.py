"""
title: Set of tests for the sounds module.
"""

import os
import unittest

from pathlib import Path

import pytest

from artbox.sounds import Sound

TMP_PATH = Path("/tmp/artbox")
TEST_DATA_DIR = Path(__file__).parent / "data"

os.makedirs(TMP_PATH, exist_ok=True)


def test_notes_to_audio():
    """
    title: Test the extraction of notes from mp3 file.
    """
    mp3_path = TMP_PATH / "set1.mp3"
    notes_path = TEST_DATA_DIR / "notes" / "set1.txt"

    params = {
        "input-path": notes_path,
        "output-path": mp3_path,
        "duration": 2,
    }
    sound = Sound(params)
    sound.notes_to_audio()


@unittest.skip("not fully implemented")
def test_extract_notes_from_mp3():
    """
    title: Test the extraction of notes from mp3 file.
    """
    filename = "pixabay-science"
    mp3_path = TEST_DATA_DIR / "audio" / f"{filename}.mp3"
    output_notes = TMP_PATH / "notes" / f"{filename}.txt"
    params = {
        "input-path": mp3_path,
        "output-path": output_notes,
    }
    sound = Sound(params)
    notes = sound.extract_notes_from_mp3()
    print("Detected notes:", notes)


@unittest.skip("not fully implemented")
def test_generate_melody():
    """
    title: Test the melody generation from notes.
    """
    notes_path = TMP_PATH / "notes" / "tok-audio.txt"
    params = {
        "input-path": notes_path,
        "output-path": "/tmp/artbox/sound.mp3",
        "duration": 3.54 * 60,
    }
    sound = Sound(params)
    sound.generate_melody()


@unittest.skip("not fully implemented")
def test_convert_to_8bit_audio():
    """
    title: Test the audio conversion to 8bits style.
    """
    input_path = TEST_DATA_DIR / "audio" / "pixabay-science.mp3"
    output_path = TMP_PATH / "sounds" / "tok8bits.mp3"
    params = {
        "input-path": mp3_path,
        "output-path": output_notes,
    }
    sound = Sound(params)
    sound.convert_to_8bit_audio()
