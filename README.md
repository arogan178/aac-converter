# aac-converter

Small script to detect AAC audio in video files and transcode the audio stream to LPCM
(pcm_s16le) while copying the video stream. Useful for editing in tools that don't support
AAC audio (e.g. DaVinci Resolve on some Linux setups).

## Files

- `convert.sh` — main script. Run with `-h` to see usage.

## Usage

Basic usage from the project root:

```bash
chmod +x convert.sh
```

```bash
./convert.sh -i /path/to/videos -o /path/to/output
```

Key options:

- `-i INPUT_DIR` — directory to search for `.mp4` files (default: current directory)
- `-o OUTPUT_DIR` — where converted files are written (defaults to input dir)
- `-a AUDIO_CODEC` — audio codec for ffmpeg (default: `pcm_s16le`; accepts `lpcm` shorthand)
- `-f FORMAT` — container format/extension for output files (default: `mov`)
- `-n` — dry-run (prints actions, does not run `ffmpeg` or delete originals)
- `-k` — keep originals (don't delete source `.mp4` after successful conversion)
- `-F` — force conversion even if audio codec isn't `aac`

Run `./convert.sh -h` for the full help text.

Notes:

- Make sure `convert.sh` is executable before running: `chmod +x convert.sh`.
- The script depends on `ffmpeg` / `ffprobe` being installed and available in PATH.
