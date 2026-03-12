# ArtBox

ArtBox is a tool set for handling multimedia files.

- Repository: https://github.com/mediatoolbox-org/artbox
- License: BSD-3-Clause

## Features

- Generate project configurations from presentation files (PDF + PPTX)
- Render narrated slide decks to MP4 from a YAML project file
- Convert text to speech and speech to text
- Download YouTube videos and captions
- Process audio and video files from the CLI

## Setup

ArtBox depends on system packages that may vary by platform. A conda or mamba
environment is recommended:

```bash
$ mamba create --name artbox "python>=3.10,<3.14" "pygobject>=3.44.1,<3.49" pip
$ conda activate artbox
$ pip install artbox
```

## Examples

For the following examples, create a temporary folder:

```bash
$ mkdir /tmp/artbox
```

### Generate a project configuration

If you exported your presentation slides as PDF and speaker notes as PPTX, you
can scaffold a project file automatically:

```bash
$ artbox init \
    --source-pdf /tmp/artbox/presentation.pdf \
    --notes-pptx /tmp/artbox/presentation.pptx \
    --output /tmp/artbox/project.yaml
```

Then render the project:

```bash
$ artbox render --project /tmp/artbox/project.yaml
```

### Convert text to audio

By default, `artbox speech` uses
[`edge-tts`](https://pypi.org/project/edge-tts/), but you can switch to
[`gtts`](https://github.com/pndurette/gTTS) with `--engine gtts`.

```bash
$ echo "Are you ready to join Link and Zelda in fighting off this unprecedented threat to Hyrule?" > /tmp/artbox/text.md
$ artbox speech from-text \
    --title artbox \
    --input-path /tmp/artbox/text.md \
    --output-path /tmp/artbox/speech.mp3 \
    --engine edge-tts
```

If you need a different language:

```bash
$ echo "Bom dia, mundo!" > /tmp/artbox/text.md
$ artbox speech from-text \
    --title artbox \
    --input-path /tmp/artbox/text.md \
    --output-path /tmp/artbox/speech.mp3 \
    --lang pt
```

For `edge-tts`, you can also specify locale, rate, volume, and pitch:

```bash
$ echo "Do you want some coffee?" > /tmp/artbox/text.md
$ artbox speech from-text \
    --title artbox \
    --input-path /tmp/artbox/text.md \
    --output-path /tmp/artbox/speech.mp3 \
    --engine edge-tts \
    --lang en-IN \
    --rate +10% \
    --volume -10% \
    --pitch -5Hz
```

### Convert audio to text

ArtBox uses `speechrecognition` for speech-to-text (currently `google` engine):

```bash
$ artbox speech to-text \
    --input-path /tmp/artbox/speech.mp3 \
    --output-path /tmp/artbox/text-from-speech.md \
    --lang en
```

### Download a YouTube video

```bash
$ artbox youtube download \
    --url https://www.youtube.com/watch?v=zw47_q9wbBE \
    --output-path /tmp/artbox/
```

To request a specific resolution:

```bash
$ artbox youtube download \
    --url https://www.youtube.com/watch?v=zw47_q9wbBE \
    --output-path /tmp/artbox/ \
    --resolution 360p
```

If you encounter bot detection, enable OAuth:

```bash
$ artbox youtube download \
    --url https://www.youtube.com/watch?v=zw47_q9wbBE \
    --output-path /tmp/artbox/ \
    --use-oauth
```

### Download YouTube captions

```bash
$ artbox youtube cc \
    --url https://www.youtube.com/watch?v=zw47_q9wbBE \
    --output-path /tmp/artbox/cc.txt \
    --lang en \
    --format text
```

### Create a song based on notes

```bash
$ echo '["E", "D#", "E", "D#", "E", "B", "D", "C", "A"]' > /tmp/artbox/notes.txt
$ artbox sound notes-to-audio \
  --input-path /tmp/artbox/notes.txt \
  --output-path /tmp/artbox/music.mp3 \
  --duration 2
```

### Generate an audio spectrogram

```bash
$ artbox sound spectrogram \
  --input-path /tmp/artbox/music.mp3 \
  --output-path /tmp/artbox/spectrogram.png
```

### Remove audio from a video

```bash
$ artbox video remove-audio \
  --input-path "/tmp/artbox/sample.mp4" \
  --output-path /tmp/artbox/video-without-audio.mp4
```

### Extract audio from a video

```bash
$ artbox video extract-audio \
  --input-path "/tmp/artbox/sample.mp4" \
  --output-path /tmp/artbox/video-audio.mp3
```

### Get metadata from a video

```bash
$ artbox video get-metadata \
  --input-path "/tmp/artbox/sample.mp4" \
  --output-path /tmp/artbox/video-metadata.json
```

### Combine audio and video files

```bash
$ artbox video combine-video-and-audio \
  --video-path /tmp/artbox/video-without-audio.mp4 \
  --audio-path /tmp/artbox/video-audio.mp3 \
  --output-path /tmp/artbox/video-combined.mp4
```

## Additional dependencies

If you want to play audio from Python, you can install `playsound`:

```bash
$ pip wheel --use-pep517 "playsound (==1.3.0)"
```
