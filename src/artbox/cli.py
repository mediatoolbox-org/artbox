"""Cli functions to define the arguments and to call Makim."""

import typer

from typing_extensions import Annotated

from artbox import __version__
from artbox.sounds import Sound
from artbox.speech import SpeechFromText, SpeechToText
from artbox.videos import Video, Youtube

app = typer.Typer(
    name="Artbox",
    help="A set of tools for handling multimedia files.",
    epilog=(
        "If you have any problem, open an issue at: "
        "https://github.com/ggpedia/artbox"
    ),
)

app_sound = typer.Typer(
    name="sound",
    help="Audio processing commands for Artbox.",
    short_help="Audio processing commands.",
)
app_video = typer.Typer(
    name="video",
    help="Video processing commands for Artbox.",
    short_help="Video processing commands.",
)
app_speech = typer.Typer(
    name="speech",
    help="Speech processing commands for Artbox.",
    short_help="Speech processing commands.",
)
app_youtube = typer.Typer(
    name="youtube",
    help="YouTube processing commands for Artbox.",
    short_help="YouTube processing commands.",
)

app.add_typer(app_sound, name="sound")
app.add_typer(app_video, name="video")
app.add_typer(app_speech, name="speech")
app.add_typer(app_youtube, name="youtube")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        is_flag=True,
        help="Show the version and exit.",
    ),
) -> None:
    """Process commands for specific flags; otherwise, show the help menu."""
    if version:
        typer.echo(f"Version: {__version__}")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)


@app_speech.command("from-text")
def speech_from_text(
    title: Annotated[
        str, typer.Option("--title", help="Specify the name of the audio file")
    ] = "artbox",
    input_path: Annotated[
        str,
        typer.Option(
            "--input-path", help="Specify the path of the text file (txt)"
        ),
    ] = "",
    output_path: Annotated[
        str,
        typer.Option(
            "--output-path", help="Specify the path to store the audio file"
        ),
    ] = "",
    engine: Annotated[
        str,
        typer.Option(
            "--engine",
            help="Choose the text-to-speech engine (Options: edge-tts, gtts)",
        ),
    ] = "edge-tts",
    lang: Annotated[
        str,
        typer.Option(
            "--lang", help="Choose the language for audio generation"
        ),
    ] = "en",
    rate: Annotated[
        str,
        typer.Option("--rate", help="Decrease/Increase the rate level"),
    ] = "+0%",
    volume: Annotated[
        str,
        typer.Option("--volume", help="Decrease/Increase the volume level"),
    ] = "+0%",
    pitch: Annotated[
        str,
        typer.Option("--pitch", help="Decrease/Increase the pitch level"),
    ] = "+0Hz",
) -> None:
    """Convert text to speech."""
    args_dict = {
        "title": title,
        "input-path": input_path,
        "output-path": output_path,
        "engine": engine,
        "lang": lang,
        "rate": rate,
        "volume": volume,
        "pitch": pitch,
    }

    runner = SpeechFromText(args_dict)
    runner.convert()


@app_speech.command("to-text")
def speech_to_text(
    input_path: Annotated[
        str,
        typer.Option(
            "--input-path",
            help="Specify the path of the audio file (mp3 or wav)",
        ),
    ] = "",
    output_path: Annotated[
        str,
        typer.Option(
            "--output-path", help="Specify the path to store the text file"
        ),
    ] = "",
    engine: Annotated[
        str,
        typer.Option(
            "--engine",
            help="Choose the text-to-speech engine (Options: google)",
        ),
    ] = "google",
    lang: Annotated[
        str,
        typer.Option(
            "--lang", help="Choose the language for audio generation"
        ),
    ] = "en",
) -> None:
    """Convert text to speech."""
    args_dict = {
        "input-path": input_path,
        "output-path": output_path,
        "engine": engine,
        "lang": lang,
    }

    runner = SpeechToText(args_dict)
    runner.convert()


@app_sound.command("notes-to-audio")
def sound_notes_to_audio(
    input_path: Annotated[
        str,
        typer.Option(
            "--input-path", help="Specify the path of the input file"
        ),
    ] = "",
    output_path: Annotated[
        str,
        typer.Option(
            "--output-path", help="Specify the path to store the audio file"
        ),
    ] = "",
    duration: Annotated[
        str,
        typer.Option("--duration", help="Specify the duration of the audio"),
    ] = "",
) -> None:
    """Convert notes to audio."""
    args_dict = {
        "input-path": input_path,
        "output-path": output_path,
        "duration": duration,
    }

    runner = Sound(args_dict)
    runner.notes_to_audio()


@app_sound.command("spectrogram")
def sound_spectrogram(
    input_path: Annotated[
        str,
        typer.Option(
            "--input-path", help="Specify the path of the input file"
        ),
    ] = "",
    output_path: Annotated[
        str,
        typer.Option(
            "--output-path", help="Specify the path to store the audio file"
        ),
    ] = "",
) -> None:
    """Generate a spectrogram from an MP3 file and saves it as an image."""
    args_dict = {
        "input-path": input_path,
        "output-path": output_path,
    }

    runner = Sound(args_dict)
    runner.spectrogram()


@app_video.command("remove-audio")
def video_remove_audio(
    input_path: Annotated[
        str,
        typer.Option(
            "--input-path", help="Specify the path of the input video file"
        ),
    ] = "",
    output_path: Annotated[
        str,
        typer.Option(
            "--output-path", help="Specify the path to store the video file"
        ),
    ] = "",
) -> None:
    """Remove audio from video file."""
    args_dict = {
        "input-path": input_path,
        "output-path": output_path,
    }

    runner = Video(args_dict)
    runner.remove_audio()


@app_video.command("extract-audio")
def video_extract_audio(
    input_path: Annotated[
        str,
        typer.Option(
            "--input-path", help="Specify the path of the input video file"
        ),
    ] = "",
    output_path: Annotated[
        str,
        typer.Option(
            "--output-path",
            help="Specify the path to store the extracted audio file",
        ),
    ] = "",
) -> None:
    """Extract audio from video file."""
    args_dict = {
        "input-path": input_path,
        "output-path": output_path,
    }

    runner = Video(args_dict)
    runner.extract_audio()


@app_video.command("get-metadata")
def video_get_metadata(
    input_path: Annotated[
        str,
        typer.Option(
            "--input-path", help="Specify the path of the input video file"
        ),
    ] = "",
    output_path: Annotated[
        str,
        typer.Option(
            "--output-path",
            help="Specify the path to store the extracted audio file",
        ),
    ] = "",
) -> None:
    """Get the metadata from a video (mp4)."""
    args_dict = {
        "input-path": input_path,
        "output-path": output_path,
    }

    runner = Video(args_dict)
    runner.get_metadata()


@app_video.command("combine-video-and-audio")
def video_combine_audio_and_video(
    video_path: Annotated[
        str,
        typer.Option(
            "--video-path", help="Specify the path of the video file"
        ),
    ] = "",
    audio_path: Annotated[
        str,
        typer.Option(
            "--audio-path", help="Specify the path of the audio file"
        ),
    ] = "",
    output_path: Annotated[
        str,
        typer.Option(
            "--output-path",
            help="Specify the path to store the combined video file",
        ),
    ] = "",
) -> None:
    """Combine audio and video files."""
    args_dict = {
        "video-path": video_path,
        "audio-path": audio_path,
        "output-path": output_path,
    }

    runner = Video(args_dict)
    runner.combine_video_and_audio()


@app_youtube.command("download")
def youtube_download(
    url: Annotated[
        str,
        typer.Option(
            "--url", help="Specify the URL of the YouTube video to download"
        ),
    ] = "",
    output_path: Annotated[
        str,
        typer.Option(
            "--output-path",
            help="Specify the path to store the downloaded video file",
        ),
    ] = "",
    resolution: Annotated[
        str,
        typer.Option(
            "--resolution", help="Set the quality of the downloaded video"
        ),
    ] = "",
    use_oauth: Annotated[
        bool,
        typer.Option(
            "--use-oauth",
            help="Use OAuth authentication to bypass bot detection",
        ),
    ] = False,
) -> None:
    """Download youtube video."""
    args_dict = {
        "url": url,
        "output-path": output_path,
        "resolution": resolution,
        "use_oauth": str(use_oauth),
    }

    runner = Youtube(args_dict)
    runner.download()


@app_youtube.command("cc")
def youtube_cc(
    url: Annotated[
        str,
        typer.Option(
            "--url", help="Specify the URL of the YouTube video to download"
        ),
    ] = "",
    output_path: Annotated[
        str,
        typer.Option(
            "--output-path",
            help=(
                "Specify the path to store the downloaded video file "
                "(.srt, .txt)"
            ),
        ),
    ] = "/tmp/cc.txt",
    lang: Annotated[
        str,
        typer.Option("--lang", help="Set the CC language to be downloaded"),
    ] = "en",
    format: Annotated[
        str,
        typer.Option("--format", help="Set the CC format (srt, text)"),
    ] = "text",
    use_oauth: Annotated[
        bool,
        typer.Option(
            "--use-oauth",
            help="Use OAuth authentication to bypass bot detection",
        ),
    ] = False,
) -> None:
    """Download youtube video CC."""
    args_dict = {
        "url": url,
        "output-path": output_path,
        "lang": lang,
        "format": format,
        "use_oauth": str(use_oauth),
    }

    runner = Youtube(args_dict)
    runner.download_captions()
