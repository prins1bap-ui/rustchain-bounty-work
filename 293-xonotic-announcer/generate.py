#!/usr/bin/env python3
"""Generate an original RustChain Arena announcer set for bounty #293.

Speech is synthesized locally with eSpeak NG and transformed with ffmpeg to an
arena-announcer texture. No recordings, stock clips, music, or external samples
are used.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
OUT = ROOT / "sounds" / "announcer"
RATE = 48_000

LINES = {
    "double_spend": "Double spend!",
    "triple_fork": "Triple fork!",
    "consensus_reached": "Consensus reached!",
    "calculating": "Calculating...",
    "building_momentum": "Building momentum!",
    "singularity": "Singularity!",
    "block_confirmed": "Block confirmed.",
    "chain_reorganization": "Chain reorganization!",
    "fifty_one_attack_detected": "Fifty one percent attack detected!",
}


def command(*parts: str) -> None:
    subprocess.run(list(parts), check=True)


def require(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"required executable not found: {name}")
    return path


def main() -> None:
    espeak = require("espeak-ng")
    ffmpeg = require("ffmpeg")
    ffprobe = require("ffprobe")
    BUILD.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    manifest = {
        "bounty": 293,
        "set": "RustChain Arena Announcer Voice Lines",
        "license": "CC0-1.0 dedication for this package; generated locally with eSpeak NG",
        "sample_rate_hz": RATE,
        "channels": 1,
        "lines": [],
    }

    for slug, text in LINES.items():
        raw = BUILD / f"{slug}-raw.wav"
        ogg = OUT / f"{slug}.ogg"
        # A lower-pitched English voice is generated locally; then audio is
        # normalized, compressed, filtered, and given a subtle arena echo.
        command(espeak, "-v", "en-us+m3", "-s", "158", "-p", "34", "-a", "190", "-w", str(raw), text)
        command(
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw),
            "-af",
            "highpass=f=90,lowpass=f=7800,acompressor=threshold=-18dB:ratio=3:attack=8:release=90,"
            "aecho=0.8:0.28:48:0.18,loudnorm=I=-16:TP=-2:LRA=7,aresample=48000",
            "-ac", "1", "-c:a", "libvorbis", "-q:a", "5", str(ogg),
        )
        probe = subprocess.check_output(
            [ffprobe, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name,sample_rate,channels,duration", "-of", "json", str(ogg)],
            text=True,
        )
        stream = json.loads(probe)["streams"][0]
        manifest["lines"].append({
            "file": str(ogg.relative_to(ROOT)),
            "text": text,
            "codec": stream["codec_name"],
            "sample_rate": int(stream["sample_rate"]),
            "channels": int(stream["channels"]),
            "duration_seconds": round(float(stream["duration"]), 3),
            "sha256": hashlib.sha256(ogg.read_bytes()).hexdigest(),
        })

    (ROOT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"generated {len(LINES)} announcer lines")


if __name__ == "__main__":
    main()
