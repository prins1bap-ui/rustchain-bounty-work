#!/usr/bin/env python3
"""Validate generated bounty #293 OGG assets without trusting filenames."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "MANIFEST.json"


def probe(path: Path) -> dict:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe is required")
    raw = subprocess.check_output([
        ffprobe, "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=codec_name,sample_rate,channels,duration",
        "-of", "json", str(path)
    ], text=True)
    return json.loads(raw)["streams"][0]


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["bounty"] == 293
    assert data["license"] == "CC0-1.0"
    assert len(data["effects"]) == 5
    seen = set()
    for item in data["effects"]:
        path = ROOT / item["file"]
        assert path.exists() and path.stat().st_size > 1000, path
        assert path.suffix == ".ogg"
        assert path.name not in seen
        seen.add(path.name)
        stream = probe(path)
        assert stream["codec_name"] == "vorbis", (path, stream)
        assert int(stream["sample_rate"]) == 48_000, (path, stream)
        assert int(stream["channels"]) == 1, (path, stream)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == item["sha256"], (path, "sha256 mismatch")
    print("validated 5/5 OGG Vorbis files: mono, 48 kHz, manifest hashes match")


if __name__ == "__main__":
    main()
