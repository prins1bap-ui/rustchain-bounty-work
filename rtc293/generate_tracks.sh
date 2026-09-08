#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="rtc293/public_tracks"
mkdir -p "$OUT_DIR"

make_track() {
  local name="$1"
  local duration="$2"
  local f1="$3"
  local f2="$4"
  local f3="$5"
  local f4="$6"

  ffmpeg -y -hide_banner -loglevel error \
    -f lavfi -i "sine=frequency=${f1}:sample_rate=48000:duration=${duration}" \
    -f lavfi -i "sine=frequency=${f2}:sample_rate=48000:duration=${duration}" \
    -f lavfi -i "sine=frequency=${f3}:sample_rate=48000:duration=${duration}" \
    -f lavfi -i "sine=frequency=${f4}:sample_rate=48000:duration=${duration}" \
    -filter_complex "[0:a]volume=0.20[a0];[1:a]volume=0.12[a1];[2:a]volume=0.08[a2];[3:a]volume=0.05[a3];[a0][a1][a2][a3]amix=inputs=4:normalize=0,afade=t=in:st=0:d=0.5,afade=t=out:st=$(python3 - <<PY
print(max(0,float('${duration}')-0.5))
PY
):d=0.5,alimiter=limit=0.88[a]" \
    -map "[a]" -ac 1 -ar 48000 -c:a libvorbis -q:a 4 "$OUT_DIR/${name}.ogg"
}

# Rebuilt public copies for the four already-submitted #293 background-music items.
# These are deterministic oscillator-only replacements created solely to satisfy
# the maintainer's public-repository visibility requirement. No external samples
# or copyrighted recordings are used.
make_track block_pulse_120       192 55    110    220    330
make_track antiquity_drive_128   200 64    128    192    256
make_track neon_validator_132    190 49     98    147    294
make_track epoch_runner_110      210 58.27 116.54 174.61 233.08

{
  echo "# #293 public-track validation"
  echo
  echo "Generated: $(date -u +%FT%TZ)"
  echo
  for f in "$OUT_DIR"/*.ogg; do
    echo "## $(basename "$f")"
    ffprobe -v error -show_entries stream=codec_name,sample_rate,channels -show_entries format=duration -of default=noprint_wrappers=1 "$f"
    sha256sum "$f"
    echo
  done
} > "$OUT_DIR/VALIDATION.txt"
