#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "double_spend.ogg",
    "triple_fork.ogg",
    "consensus_reached.ogg",
    "calculating.ogg",
    "building_momentum.ogg",
    "singularity.ogg",
    "block_confirmed.ogg",
    "chain_reorganization.ogg",
    "fifty_one_attack_detected.ogg",
}


def main() -> None:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe is required")
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["bounty"] == 293
    assert len(manifest["lines"]) == 9
    found = {Path(x["file"]).name for x in manifest["lines"]}
    assert found == EXPECTED, (found, EXPECTED)
    for item in manifest["lines"]:
        path = ROOT / item["file"]
        assert path.exists() and path.stat().st_size > 1000, path
        raw = subprocess.check_output([
            ffprobe, "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=codec_name,sample_rate,channels,duration",
            "-of", "json", str(path)
        ], text=True)
        stream = json.loads(raw)["streams"][0]
        assert stream["codec_name"] == "vorbis"
        assert int(stream["sample_rate"]) == 48_000
        assert int(stream["channels"]) == 1
        assert 0.25 < float(stream["duration"]) < 8.0
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    print("validated 9/9 announcer OGG files: Vorbis, mono, 48 kHz, hashes match")


if __name__ == "__main__":
    main()
