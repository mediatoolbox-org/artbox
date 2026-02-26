# ArtBox

ArtBox is a tool set for handling multimedia files.

- Documentation: https://ggpedia.games
- License: BSD-3 Clause

## Features

TBD

# Setup

ArtBox uses some dependencies that maybe would not work well in your machine. In
order to have everything well installed, create a conda/mamba environment and
install `artbox` there.

```bash
$ mamba create --name artbox "python>=3.10,<3.14" "pygobject>=3.44.1,<3.49" pip
$ conda activate artbox
$ pip install artbox
```

## Examples

For the following examples, create the a temporary folder for artbox:

```bash
$ mkdir /tmp/artbox
```

### Generate a project configuration

If you have exported your presentation slides as a PDF and your presentation
notes as a PPTX from tools like Canva, you can automatically generate an
`artbox` project configuration file:

```bash
$ artbox init \
    --source-pdf /tmp/artbox/presentation.pdf \
    --notes-pptx /tmp/artbox/presentation.pptx \
    --output /tmp/artbox/project.yaml
```

This will extract the speaker notes for every slide and automatically format a
`.yaml` file that is ready to be parsed by `artbox render`.

### Convert text to audio

By default, the `artbox speech` uses
[`edge-tts`](https://pypi.org/project/edge-tts/) engine, but if you can also
specify [`gtts`](https://github.com/pndurette/gTTS) with the flag
`--engine gtts`.

```bash
$ echo "Are you ready to join Link and Zelda in fighting off this unprecedented threat to Hyrule?" > /tmp/artbox/text.md
$ artbox speech from-text \
    --title artbox \
    --input-path /tmp/artbox/text.md \
    --output-path /tmp/artbox/speech.mp3 \
    --engine edge-tts
```

If you need to generate the audio for different language, you can use the flag
`--lang`:

```bash
$ echo "Bom dia, mundo!" > /tmp/artbox/text.md
$ artbox speech from-text \
    --title artbox \
    --input-path /tmp/artbox/text.md \
    --output-path /tmp/artbox/speech.mp3 \
    --lang pt
```

If you are using `edge-tts` engine (the default one), you can also specify the
locale for that language, for example:

```bash
$ echo "Are you ready to join Link and Zelda in fighting off this unprecedented threat to Hyrule?" > /tmp/artbox/text.md
$ artbox speech from-text \
    --title artbox \
    --input-path /tmp/artbox/text.md \
    --output-path /tmp/artbox/speech.mp3 \
    --engine edge-tts \
    --lang en-IN
```

Additionally, if you are using edge-tts, you can specify `--rate`, `--volume`,
and `--pitch`, for example:

```bash
$ echo "Do you want some coffee?" > /tmp/artbox/text.md
$ artbox speech from-text \
    --title artbox \
    --input-path /tmp/artbox/text.md \
    --output-path /tmp/artbox/speech.mp3 \
    --engine edge-tts \
    --lang en \
    --rate +10% \
    --volume -10% \
    --pitch -5Hz
```

### Convert audio to text

ArtBox uses `speechrecognition` to convert from audio to text. Currently, ArtBox
just support the `google` engine.

For this example, let's first create our audio:

```bash
$ echo "Are you ready to join Link and Zelda in fighting off this unprecedented threat to Hyrule?" > /tmp/artbox/text.md
$ artbox speech from-text \
    --title artbox \
    --input-path /tmp/artbox/text.md \
    --output-path /tmp/artbox/speech.mp3 \
    --engine edge-tts
```

Now we can convert it back to text:

```bash
$ artbox speech to-text \
    --input-path /tmp/artbox/speech.mp3 \
    --output-path /tmp/artbox/text-from-speech.md \
    --lang en
```

### Download a youtube video

If you want to download videos from the youtube, you can use the following
command:

```bash
$ artbox youtube download \
    --url https://www.youtube.com/watch?v=zw47_q9wbBE \
    --output-path /tmp/artbox/
```

The command above downloads using a random resolution. If you want a specific
resolution, use the flag `--resolution`:

```bash
$ artbox youtube download \
    --url https://www.youtube.com/watch?v=zw47_q9wbBE \
    --output-path /tmp/artbox/ \
    --resolution 360p
```

If you encounter bot detection errors, use the `--use-oauth` flag to
authenticate via your Google account. The first time you use it, you will be
prompted to open a URL and enter a code. Credentials are cached for subsequent
downloads:

```bash
$ artbox youtube download \
    --url https://www.youtube.com/watch?v=zw47_q9wbBE \
    --output-path /tmp/artbox/ \
    --use-oauth
```

### Create a song based on the musical notes

```bash
# json format
echo '["E", "D#", "E", "D#", "E", "B", "D", "C", "A"]' > /tmp/artbox/notes.txt
$ artbox sound notes-to-audio \
  --input-path /tmp/artbox/notes.txt \
  --output-path /tmp/artbox/music.mp3 \
  --duration 2
```

### Remove the audio from a video

First, download the youtube video `https://www.youtube.com/watch?v=zw47_q9wbBE`
as explained before.

Next, run the following command:

```bash
$ artbox video remove-audio \
  --input-path "/tmp/artbox/The Legend of Zelda Breath of the Wild - Nintendo Switch Presentation 2017 Trailer.mp4" \
  --output-path /tmp/artbox/botw.mp4
```

### Extract the audio from a video

First, download the youtube video `https://www.youtube.com/watch?v=zw47_q9wbBE`
as explained before.

Next, run the following command:

```bash
$ artbox video extract-audio \
  --input-path "/tmp/artbox/The Legend of Zelda Breath of the Wild - Nintendo Switch Presentation 2017 Trailer.mp4" \
  --output-path /tmp/artbox/botw-audio.mp3
```

### Combine audio and video files

First, execute the previous steps:

- Download a youtube video
- Remove the audio from a video
- Extract the audio from a video

Next, run the following command:

```bash
$ artbox video combine-video-and-audio \
  --video-path /tmp/artbox/botw.mp4 \
  --audio-path /tmp/artbox/botw-audio.mp3 \
  --output-path /tmp/artbox/botw-combined.mp4
```

## Additional dependencies

If you want to use Python to play your audio files, you can install `playsound`:

```bash
$ pip wheel --use-pep517 "playsound (==1.3.0)"
```
