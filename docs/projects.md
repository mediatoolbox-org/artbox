# Artbox Projects

An **artbox project** allows you to automate the creation of video presentations
by combining static visual slides (such as a PDF or image folder) with dynamic
text-to-speech (TTS) audio. Instead of manually recording voice-overs and
syncing them to a timeline in a video editor, you can orchestrate an entire
presentation natively through a single YAML configuration file.

This guide will walk you through automatically scaffolding a project from your
presentation notes, understanding the project schema, and rendering it into a
final MP4 video.

---

## 1. Initializing a Project

If you build your presentations in software like Canva, PowerPoint, or Google
Slides, you usually export your slides as a PDF. More importantly, those
platforms allow you to export your "Speaker Notes" as a `.pptx` file.

Artbox can automatically pair these two artifacts together to scaffold your
project for you.

To generate a project, run the `init` command:

```bash
artbox init \
    --source-pdf presentation.pdf \
    --notes-pptx notes_with_speaker_text.pptx \
    --output my_project.yaml
```

This command parses your presentation, aligns each slide in the PDF with its
corresponding speaker notes, and generates a ready-to-render `my_project.yaml`
configuration file.

---

## 2. Understanding the Project Schema

Open the generated `my_project.yaml` file. It acts as the "director's script"
for the video rendering engine.

The YAML relies on three massive foundational pillars: **audio**, **video**, and
**slides**. Here is a high-level look at the structure:

```yaml
name: my_project
cache-dir: my-saved-artifacts # (Optional) Directory to save intermediate resources
source:
  type: pdf
  path: presentation.pdf

# Video Engine Configuration
video:
  engine: ffmpeg

# Audio Engine Configuration
audio:
  engine: openai-tts
  instruction: "" # (Optional) Path to a text file with advanced voice prompt instructions
  defaults:
    gender: male
    language: en
    model: tts-1
    pitch: 1.0
    speed: 1.0
    volume: 1.0

# Slides Timeline
slides:
  defaults:
    transitions:
      pause-after: 3.0
  items:
    - slide: 1
      background:
        page: 1
      audio:
        text: >
          Hello world! Welcome to the presentation!
```

### Global Configuration Blocks

- **`cache-dir`** _(Optional)_: Artbox securely orchestrates videos by spinning
  up localized `/tmp` resources for audio loops and image framing, which are
  explicitly garbage-collected before returning your output `MP4`. If you
  declare a `cache-dir`, the intermediate cropped background png files and AI
  `.mp3` generations will be permanently persisted here instead of deleted!
- **`video.engine`**: The backend framework building your MP4. It natively
  supports `ffmpeg` (fast, lightweight) or `moviepy` (robust framing).
- **`audio.engine`**: The backend framework resolving text-to-speech. Supports
  `edge-tts`, `gtts`, or `openai-tts`.
- **`audio.instruction`** _(Optional)_: If your selected audio engine supports
  system-prompting (like OpenAI's experimental streaming models), you can point
  this to a text file (e.g., `/tmp/voice-rules.md`). The engine will read the
  file and inject those instructions directly into the TTS generation!
- **`audio.defaults`**: These are the baseline metrics applied to all slides.

### The Slides Timeline

The `slides` property houses the sequence of your video. It defines `defaults`
for slide transitions (like how many empty seconds string the slides together)
and a list of `items` that map to physical rendering frames.

Notice how slide 1 natively overrides the audio `text`. Because `artbox`
operates on a hierarchy, **you can override global audio properties on a
per-slide basis!**

For example, if slide 2 needs to speak faster and use a deeper pitch, you can
explicitly configure it in the `items` block:

```yaml
- slide: 2
  background:
    page: 2
  audio:
    text: >
      This text will be spoken twice as fast!
    speed: 2.0
    pitch: -20
```

---

## 3. Rendering the Video

Once your YAML script is ready to go, the final step is incredibly simple. Pass
your project configuration to the `artbox render` pipeline:

```bash
artbox render my_project.yaml
```

_Note: If you are utilizing the `openai-tts` audio engine, ensure you have
exported your `OPENAI_API_KEY` to your environment beforehand, or pass it via
the CLI like so:_

```bash
artbox --env-file .env render my_project.yaml
```

Artbox will sequentially parse every slide, generate high definition images from
your PDF, synthesize native audio tracks for every slide block, and stitch the
entire timeline together into a pristine MP4 file!
