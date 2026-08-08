#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export SILICON_FURY_HEADLESS=1
export SDL_VIDEODRIVER=dummy
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

DEMOS=(
  01-title-teams
  02-character-select
  03-versus-brawl
  04-special-moves
  05-story-ko
)

mkdir -p media/frames media/gifs media/videos

for d in "${DEMOS[@]}"; do
  echo "== Recording $d =="
  rm -rf "media/frames/$d"
  python3 main.py --demo "$d" --capture-dir media/frames
  # Build smooth 20fps GIF from PNG sequence (full frame, no crop)
  ffmpeg -y -framerate 20 -i "media/frames/$d/frame_%04d.png" \
    -vf "scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=192:stats_mode=full[p];[s1][p]paletteuse=dither=sierra2_4a" \
    -loop 0 "media/gifs/${d}.gif"
  # Also keep MP4
  ffmpeg -y -framerate 20 -i "media/frames/$d/frame_%04d.png" \
    -c:v libx264 -pix_fmt yuv420p -crf 20 "media/videos/${d}.mp4"
  echo "Wrote media/gifs/${d}.gif"
done

ls -lh media/gifs/
