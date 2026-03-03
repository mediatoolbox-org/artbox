"""
title: Tests for the render module.
"""

import os
import tempfile

from pathlib import Path

import pytest
import yaml

from jsonschema import ValidationError

from artbox.render import (
    Render,
    _float_to_edge_tts_percent,
    _float_to_edge_tts_pitch,
    _resolve_language,
)


TMP_PATH = Path("/tmp/artbox")
os.makedirs(TMP_PATH, exist_ok=True)


# --- Unit tests for helper functions ---


class TestHelperFunctions:
    """
    title: Tests for converter and resolver helper functions.
    """

    def test_float_to_percent_neutral(self):
        """
        title: Test neutral volume/speed conversion.
        """
        assert _float_to_edge_tts_percent(1.0) == "+0%"

    def test_float_to_percent_decrease(self):
        """
        title: Test decreased volume/speed conversion.
        """
        assert _float_to_edge_tts_percent(0.8) == "-20%"

    def test_float_to_percent_increase(self):
        """
        title: Test increased volume/speed conversion.
        """
        assert _float_to_edge_tts_percent(1.1) == "+10%"

    def test_float_to_pitch_neutral(self):
        """
        title: Test neutral pitch conversion.
        """
        assert _float_to_edge_tts_pitch(1.0) == "+0Hz"

    def test_float_to_pitch_increase(self):
        """
        title: Test increased pitch conversion.
        """
        assert _float_to_edge_tts_pitch(1.2) == "+40Hz"

    def test_float_to_pitch_decrease(self):
        """
        title: Test decreased pitch conversion.
        """
        assert _float_to_edge_tts_pitch(0.9) == "-20Hz"

    def test_resolve_language_named(self):
        """
        title: Test language name resolution.
        """
        assert _resolve_language("spanish") == "es"
        assert _resolve_language("English") == "en"

    def test_resolve_language_code(self):
        """
        title: Test language code passthrough.
        """
        assert _resolve_language("pt") == "pt"
        assert _resolve_language("en-US") == "en-US"


# --- Schema validation tests ---


def _make_valid_config() -> dict:
    """
    title: Create a minimal valid project configuration.
    returns:
      type: dict
    """
    return {
        "name": "test-project",
        "audio": {
            "engine": "openai-tts",
            "defaults": {
                "language": "english",
                "gender": "female",
                "volume": 1.0,
                "pitch": 1.0,
                "speed": 1.0,
            },
        },
        "video": {"engine": "ffmpeg"},
        "source": {"type": "image"},
        "slides": {
            "defaults": {"transitions": {"pause-after": 3}},
            "items": [
                {
                    "slide": 1,
                    "background": {"path": "slide1.png"},
                    "audio": {"text": "Hello world"},
                    "pause-after": 2,
                }
            ],
        },
    }


class TestSchemaValidation:
    """
    title: Tests for YAML schema validation.
    """

    def test_valid_config(self):
        """
        title: Test that a valid configuration passes validation.
        """
        renderer = Render()
        config = _make_valid_config()

        with tempfile.NamedTemporaryFile(
            suffix=".yaml", mode="w", delete=False
        ) as f:
            yaml.dump(config, f)
            tmp_path = f.name

        try:
            result = renderer.load_and_validate(tmp_path)
            assert result["name"] == "test-project"
            assert len(result["slides"]["items"]) == 1
        finally:
            os.unlink(tmp_path)

    def test_valid_pdf_config(self):
        """
        title: Test that a valid PDF configuration passes validation.
        """
        renderer = Render()
        config = _make_valid_config()
        config["source"] = {"type": "pdf", "path": "slides.pdf"}
        config["slides"]["items"][0]["background"] = {"page": 1}

        with tempfile.NamedTemporaryFile(
            suffix=".yaml", mode="w", delete=False
        ) as f:
            yaml.dump(config, f)
            tmp_path = f.name

        try:
            result = renderer.load_and_validate(tmp_path)
            assert result["source"]["type"] == "pdf"
        finally:
            os.unlink(tmp_path)

    def test_missing_name_raises(self):
        """
        title: Test that missing 'name' field raises ValidationError.
        """
        renderer = Render()
        config = _make_valid_config()
        del config["name"]

        with tempfile.NamedTemporaryFile(
            suffix=".yaml", mode="w", delete=False
        ) as f:
            yaml.dump(config, f)
            tmp_path = f.name

        try:
            with pytest.raises(ValidationError):
                renderer.load_and_validate(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_missing_slides_raises(self):
        """
        title: Test that missing 'slides' field raises ValidationError.
        """
        renderer = Render()
        config = _make_valid_config()
        del config["slides"]

        with tempfile.NamedTemporaryFile(
            suffix=".yaml", mode="w", delete=False
        ) as f:
            yaml.dump(config, f)
            tmp_path = f.name

        try:
            with pytest.raises(ValidationError):
                renderer.load_and_validate(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_invalid_source_type_raises(self):
        """
        title: Test that an invalid source type raises ValidationError.
        """
        renderer = Render()
        config = _make_valid_config()
        config["source"]["type"] = "docx"

        with tempfile.NamedTemporaryFile(
            suffix=".yaml", mode="w", delete=False
        ) as f:
            yaml.dump(config, f)
            tmp_path = f.name

        try:
            with pytest.raises(ValidationError):
                renderer.load_and_validate(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_invalid_gender_raises(self):
        """
        title: Test that an invalid gender raises ValidationError.
        """
        renderer = Render()
        config = _make_valid_config()
        config["audio"]["defaults"]["gender"] = "robot"

        with tempfile.NamedTemporaryFile(
            suffix=".yaml", mode="w", delete=False
        ) as f:
            yaml.dump(config, f)
            tmp_path = f.name

        try:
            with pytest.raises(ValidationError):
                renderer.load_and_validate(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_extra_field_raises(self):
        """
        title: Test that extra fields raise ValidationError.
        """
        renderer = Render()
        config = _make_valid_config()
        config["unexpected_field"] = "bad"

        with tempfile.NamedTemporaryFile(
            suffix=".yaml", mode="w", delete=False
        ) as f:
            yaml.dump(config, f)
            tmp_path = f.name

        try:
            with pytest.raises(ValidationError):
                renderer.load_and_validate(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_cache_dir_valid(self):
        """
        title: Test that adding a cache-dir property is valid.
        """
        renderer = Render()
        config = _make_valid_config()
        config["cache-dir"] = "my_cache_test_dir"

        with tempfile.NamedTemporaryFile(
            suffix=".yaml", mode="w", delete=False
        ) as f:
            yaml.dump(config, f)
            tmp_path = f.name

        try:
            result = renderer.load_and_validate(tmp_path)
            assert result["cache-dir"] == "my_cache_test_dir"
        finally:
            os.unlink(tmp_path)
