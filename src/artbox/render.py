"""Render module for building videos from YAML project configurations."""

from __future__ import annotations

import json
import os
import tempfile

from pathlib import Path

import yaml

from jsonschema import validate
from PIL import Image

from artbox.engines import BaseVideoEngine, FFmpegEngine, MoviePyEngine
from artbox.speech import SpeechFromText

# Language name -> edge-tts language code mapping
LANGUAGE_MAP: dict[str, str] = {
    "spanish": "es",
    "english": "en",
    "portuguese": "pt",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "japanese": "ja",
    "chinese": "zh",
    "korean": "ko",
    "russian": "ru",
    "arabic": "ar",
    "hindi": "hi",
    "dutch": "nl",
    "polish": "pl",
    "turkish": "tr",
    "swedish": "sv",
    "norwegian": "nb",
    "danish": "da",
    "finnish": "fi",
    "greek": "el",
}

SCHEMA_PATH = Path(__file__).parent / "schema.json"


def _load_schema() -> dict:
    """Load the JSON schema for project validation."""
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)


def _float_to_edge_tts_percent(value: float) -> str:
    """
    Convert a float multiplier to an edge-tts percentage string.

    Parameters
    ----------
    value : float
        Multiplier where 1.0 is neutral (e.g., 0.8 = -20%, 1.1 = +10%).

    Returns
    -------
    str
        Formatted string like ``"+10%"`` or ``"-20%"``.
    """
    pct = round((value - 1.0) * 100)
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct}%"


def _float_to_edge_tts_pitch(value: float) -> str:
    """
    Convert a float pitch multiplier to an edge-tts Hz offset string.

    Parameters
    ----------
    value : float
        Multiplier where 1.0 is neutral.

    Returns
    -------
    str
        Formatted string like ``"+40Hz"`` or ``"-10Hz"``.
    """
    hz = round((value - 1.0) * 200)
    sign = "+" if hz >= 0 else ""
    return f"{sign}{hz}Hz"


def _resolve_language(lang_str: str) -> str:
    """
    Resolve a language name or code to an edge-tts language code.

    Parameters
    ----------
    lang_str : str
        Language name (e.g. ``"spanish"``) or code (e.g. ``"es"``).

    Returns
    -------
    str
        A short language code suitable for edge-tts.
    """
    lower = lang_str.lower()
    return LANGUAGE_MAP.get(lower, lang_str)


class Render:
    """Orchestrate building a video from a YAML project configuration."""

    def __init__(self) -> None:
        """Initialize the Render instance."""
        self._schema = _load_schema()
        self._tmp_files: list[str] = []

    def load_and_validate(self, project_path: str) -> dict:
        """
        Load a YAML project file and validate it against the schema.

        Parameters
        ----------
        project_path : str
            Path to the YAML project file.

        Returns
        -------
        dict
            The parsed and validated project configuration.

        Raises
        ------
        jsonschema.ValidationError
            If the YAML does not conform to the schema.
        """
        with open(project_path, "r") as f:
            config = yaml.safe_load(f)

        validate(instance=config, schema=self._schema)
        return config

    def _resolve_background(
        self,
        slide_config: dict,
        source_config: dict,
        project_dir: str,
    ) -> str:
        """
        Resolve the background image path for a slide; ensure even dimensions.

        Parameters
        ----------
        slide_config : dict
            The slide configuration dictionary.
        source_config : dict
            The project-level source configuration.
        project_dir : str
            Directory of the project YAML (for relative path resolution).

        Returns
        -------
        str
            Absolute path to the background image file with even dimensions.
        """
        bg = slide_config.get("background", {})
        source_type = source_config.get("type", "image")

        if source_type == "image":
            img_path = bg.get("path", "")
            resolved = Path(project_dir) / img_path

            img = Image.open(resolved)
            w, h = img.size
            if w % 2 != 0 or h % 2 != 0:
                new_w = w - (w % 2)
                new_h = h - (h % 2)
                resized_img = img.resize((new_w, new_h))
                tmp_file = tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False
                )
                resized_img.save(tmp_file.name, "PNG")
                self._tmp_files.append(tmp_file.name)
                return tmp_file.name

            return str(resolved.resolve())

        if source_type == "pdf":
            from pdf2image import convert_from_path  # noqa: PLC0415

            pdf_path = str(
                (Path(project_dir) / source_config["path"]).resolve()
            )
            page_num = bg.get("page", 1)

            images = convert_from_path(
                pdf_path,
                first_page=page_num,
                last_page=page_num,
                dpi=200,
            )

            pdf_img = images[0]
            w, h = pdf_img.size
            if w % 2 != 0 or h % 2 != 0:
                new_w = w - (w % 2)
                new_h = h - (h % 2)
                resized_img = pdf_img.resize((new_w, new_h))
                tmp_file = tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False
                )
                resized_img.save(tmp_file.name, "PNG")
            else:
                tmp_file = tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False
                )
                pdf_img.save(tmp_file.name, "PNG")

            self._tmp_files.append(tmp_file.name)
            return tmp_file.name

        raise ValueError(f"Unknown source type: {source_type}")

    def _generate_audio(
        self,
        slide_config: dict,
        audio_config_root: dict,
        project_dir: str,
    ) -> str | None:
        """
        Generate or resolve the audio file for a slide.

        Parameters
        ----------
        slide_config : dict
            The slide configuration dictionary.
        audio_config_root : dict
            The root audio settings block from the project config.
        project_dir : str
            Directory of the project YAML (for relative path resolution).

        Returns
        -------
        str or None
            Path to the audio file, or None if no audio is configured.
        """
        audio_config = slide_config.get("audio")
        if not audio_config:
            return None

        # Pre-recorded audio file
        if "path" in audio_config:
            audio_path = Path(project_dir) / audio_config["path"]
            return str(audio_path.resolve())

        # Text-to-speech
        if "text" in audio_config:
            text = audio_config["text"]

            # Resolve parameters (per-slide overrides global)
            defaults = audio_config_root.get("defaults", {})
            volume = audio_config.get("volume", defaults.get("volume", 1.0))
            speed = audio_config.get("speed", defaults.get("speed", 1.0))
            pitch = audio_config.get("pitch", defaults.get("pitch", 1.0))
            lang = _resolve_language(defaults.get("language", "en"))
            gender = defaults.get("gender", "female")
            voice_id = audio_config.get("voice-id", defaults.get("voice-id"))
            model = audio_config.get("model", defaults.get("model", "tts-1"))

            # Write text to a temp file for SpeechFromText
            text_file = tempfile.NamedTemporaryFile(
                suffix=".txt", delete=False, mode="w"
            )
            text_file.write(text)
            text_file.close()
            self._tmp_files.append(text_file.name)

            audio_file = tempfile.NamedTemporaryFile(
                suffix=".mp3", delete=False
            )
            audio_file.close()
            self._tmp_files.append(audio_file.name)

            tts_engine = audio_config_root.get("engine", "edge-tts")
            instruction = audio_config_root.get("instruction", "")

            args = {
                "title": "artbox-render",
                "input-path": text_file.name,
                "output-path": audio_file.name,
                "engine": tts_engine,
                "lang": lang,
                "rate": _float_to_edge_tts_percent(speed),
                "volume": _float_to_edge_tts_percent(volume),
                "pitch": _float_to_edge_tts_pitch(pitch),
                "gender": gender.capitalize(),
                "model": model,
            }
            if voice_id is not None:
                args["voice_id"] = voice_id
            if instruction:
                args["instruction"] = instruction

            speech = SpeechFromText(args)
            speech.convert()

            return audio_file.name

        return None

    def render(self, project_path: str, output_dir: str | None = None) -> str:
        """
        Build the final MP4 video from a YAML project configuration.

        Parameters
        ----------
        project_path : str
            Path to the YAML project file.
        output_dir : str or None
            Output directory for the video. If None, uses the ``output``
            field from the YAML config.

        Returns
        -------
        str
            Path to the generated MP4 file.
        """
        config = self.load_and_validate(project_path)
        project_dir = str(Path(project_path).parent)

        # Determine output directory
        out_dir = output_dir or config.get("output", "/tmp/artbox")
        os.makedirs(out_dir, exist_ok=True)

        audio_config_root = config.get("audio", {})
        video_config_root = config.get("video", {})
        slides_root = config.get("slides", {})

        global_pause = (
            slides_root.get("defaults", {})
            .get("transitions", {})
            .get("pause-after", 3.0)
        )
        source_config = config.get("source", {"type": "image"})

        slides_items = slides_root.get("items", [])

        # Determine engine
        engine_type = video_config_root.get("engine", "moviepy")
        engine: BaseVideoEngine

        project_name = config.get("name", "output")
        output_path = str(Path(out_dir) / f"{project_name}.mp4")

        if engine_type == "ffmpeg":
            engine = FFmpegEngine(output_path, fps=24)
        else:
            engine = MoviePyEngine(output_path, fps=24)

        try:
            for slide in slides_items:
                slide_num = slide.get("slide", 0)
                print(f"Processing slide {slide_num}...")

                # Resolve background
                image_path = self._resolve_background(
                    slide, source_config, project_dir
                )

                # Generate or resolve audio
                audio_path = self._generate_audio(
                    slide, audio_config_root, project_dir
                )

                # Determine pause-after (slide-level > audio-level > global)
                audio_config = slide.get("audio", {})
                pause = slide.get(
                    "pause-after",
                    audio_config.get("pause-after", global_pause),
                )

                # Add slide to engine
                engine.add_slide(image_path, audio_path, pause)

            # Render the video using the orchestrated engine
            engine.render()

            print(
                f"Video rendered successfully: {output_path} "
                f"using {engine_type} engine."
            )
            return output_path

        finally:
            # Clean up temp files
            for tmp_file in self._tmp_files:
                try:
                    os.unlink(tmp_file)
                except OSError:
                    pass
            self._tmp_files.clear()
