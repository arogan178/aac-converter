#!/usr/bin/env bash

# convert.sh - transcode audio in video files (AAC -> other codec) while copying video
# Usage: convert.sh [-i input_dir] [-o output_dir] [-a audio_codec] [-f format] [-j jobs] [-n] [-k] [-F] [-h]
#   -i INPUT_DIR   Directory to search for video files (default: current dir)
#   -o OUTPUT_DIR  Directory to write converted files (default: INPUT_DIR)
#   -a AUDIO_CODEC Target audio codec for ffmpeg (default: ac3)
#   -f FORMAT      Container/format for output files (default: mov)
#   -j JOBS        Number of parallel conversion jobs (default: 1)
#   -n             Dry-run: show what would be done but don't run ffmpeg or delete files
#   -k             Keep original files (don't delete after successful conversion)
#   -F             Force: transcode regardless of detected audio codec
#   -h             Show this help message

set -o errexit
set -o nounset
set -o pipefail

INPUT_DIR="."
OUTPUT_DIR=""
DRY_RUN=0
KEEP_ORIGINAL=0
FORCE=0
MAX_JOBS=1
## Default to LPCM (signed 16-bit little-endian PCM) which many editors accept
AUDIO_CODEC="pcm_s16le"
FORMAT="mov"

log() {
  echo "$(date '+%H:%M:%S') $1"
}

print_help() {
  sed -n '1,200p' "$0" | sed -n '1,20p'
  echo
  echo "Example: $0 -i /path/to/input -o /path/to/output"
}

while getopts ":i:o:nkha:f:Fj:" opt; do
  case $opt in
    i) INPUT_DIR="$OPTARG" ;;
    o) OUTPUT_DIR="$OPTARG" ;;
    n) DRY_RUN=1 ;;
    k) KEEP_ORIGINAL=1 ;;
    a) 
      # accept shorthand 'lpcm' for pcm_s16le
      if [ "$OPTARG" = "lpcm" ] || [ "$OPTARG" = "LPCM" ]; then
        AUDIO_CODEC="pcm_s16le"
      else
        AUDIO_CODEC="$OPTARG"
      fi
      ;;
  f) FORMAT="$OPTARG" ;;
  F) FORCE=1 ;;
  j) MAX_JOBS="$OPTARG" ;;
  h) print_help; exit 0 ;;
    \?) echo "Unknown option: -$OPTARG" >&2; print_help; exit 2 ;;
    :) echo "Missing argument for -$OPTARG" >&2; print_help; exit 2 ;;
  esac
done

# If no output dir provided, default to input dir
if [ -z "$OUTPUT_DIR" ]; then
  OUTPUT_DIR="$INPUT_DIR"
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Error: ffmpeg not found in PATH. Install ffmpeg and retry." >&2
  exit 3
fi

if ! command -v ffprobe >/dev/null 2>&1; then
  echo "Error: ffprobe not found in PATH. ffprobe (part of ffmpeg) is required for audio detection." >&2
  exit 3
fi

if [ ! -d "$INPUT_DIR" ]; then
  echo "Error: input directory '$INPUT_DIR' does not exist or is not a directory." >&2
  exit 4
fi

# Create output dir if needed
if [ ! -d "$OUTPUT_DIR" ]; then
  echo "Output directory '$OUTPUT_DIR' does not exist. Creating..."
  if [ $DRY_RUN -eq 0 ]; then
    mkdir -p "$OUTPUT_DIR"
  else
    echo "(dry-run) would create: $OUTPUT_DIR"
  fi
fi

echo "Input dir:   $INPUT_DIR"
echo "Output dir:  $OUTPUT_DIR"
echo "Audio codec: $AUDIO_CODEC"
echo "Format:      $FORMAT"
if [ $DRY_RUN -eq 1 ]; then
  echo "Mode:       dry-run (no ffmpeg, no deletion)"
fi
if [ $KEEP_ORIGINAL -eq 1 ]; then
  echo "Behavior:   keeping original video files after successful conversion"
fi
if [ $MAX_JOBS -gt 1 ]; then
  log "Mode:       parallel ($MAX_JOBS jobs)"
fi

# Find .mp4 files (non-recursive) and process them safely
shopt -s nullglob
shopt -s nocaseglob
cd "$INPUT_DIR"

OUT_EXT="$FORMAT"

for fn in *.mp4 *.mov *.avi *.mkv *.webm; do
  # If no files match, the loop will be skipped because of nullglob
  if [ ! -f "$fn" ]; then
    continue
  fi
  log "Found: $fn"
  base="${fn%.*}"
  output_fn="$OUTPUT_DIR/${base}.${OUT_EXT}"

  # Detect first audio stream codec (a:0)
  audio_codec_detected=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "$fn" 2>/dev/null || echo "")

  if [ -z "$audio_codec_detected" ]; then
    echo "  No audio stream detected in '$fn' — skipping"
    continue
  fi

  # Count number of audio streams
  num_audio=$(ffprobe -v error -select_streams a -show_entries stream=index -of default=noprint_wrappers=1:nokey=1 "$fn" 2>/dev/null | wc -l)

  echo "  Detected audio codec: $audio_codec_detected"
  echo "  Number of audio tracks: $num_audio"

  if [ "$audio_codec_detected" != "aac" ] && [ $FORCE -eq 0 ]; then
    echo "  Audio is not AAC and -F (force) not set; skipping $fn"
    continue
  fi

  # Set audio codec option: copy if multiple tracks, else transcode
  if [ $num_audio -gt 1 ]; then
    audio_option="-c:a copy"
  else
    audio_option="-c:a $AUDIO_CODEC"
  fi

  if [ $DRY_RUN -eq 1 ]; then
    echo "(dry-run) ffmpeg -i '$INPUT_DIR/$fn' -n -c:v copy $audio_option -f $FORMAT '$output_fn'"
    if [ $KEEP_ORIGINAL -eq 0 ]; then
      echo "(dry-run) would remove '$INPUT_DIR/$fn' after successful conversion (unless -k)"
    else
      echo "(dry-run) would keep original '$INPUT_DIR/$fn' (because -k was set)"
    fi
    continue
  fi

  # Run ffmpeg: copy video, transcode audio
  if [ $MAX_JOBS -gt 1 ] && [ $DRY_RUN -eq 0 ]; then
    # Parallel mode: run in background
    ffmpeg -progress /dev/stdout -i "$fn" -n -c:v copy $audio_option -f "$FORMAT" "$output_fn" 2>/dev/null &
    log "  Started conversion: $fn"
  else
    # Sequential mode
    if ffmpeg -progress /dev/stdout -i "$fn" -n -c:v copy $audio_option -f "$FORMAT" "$output_fn" 2>/dev/null; then
      log "  ✓ Converted: $fn -> $output_fn"
      if [ $KEEP_ORIGINAL -eq 0 ]; then
        rm -- "$fn"
        log "  Removed original: $fn"
      else
        log "  Keeping original: $fn"
      fi
    else
      log "  ✗ Skipped (ffmpeg failed): $fn"
    fi
  fi
done

if [ $MAX_JOBS -gt 1 ] && [ $DRY_RUN -eq 0 ]; then
  wait
  log "All conversions completed"
fi

shopt -u nullglob

