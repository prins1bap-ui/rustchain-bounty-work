#!/usr/bin/env python3
"""Generate an original five-effect RustChain Arena weapon SFX set.

All audio is synthesized from deterministic mathematical waveforms and seeded
noise. No samples, recordings, or third-party media are used.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import shutil
import struct
import subprocess
import wave
from pathlib import Path

RATE = 48_000
ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
OUT = ROOT / "sounds" / "weapons"


def clamp(x: float) -> float:
    return max(-0.98, min(0.98, x))


def env(t: float, duration: float, attack: float = 0.01, release: float = 0.20) -> float:
    a = min(1.0, t / max(attack, 1e-6))
    r = min(1.0, max(0.0, duration - t) / max(release, 1e-6))
    return min(a, r)


def noise(rng: random.Random) -> float:
    return rng.uniform(-1.0, 1.0)


def write_wav(name: str, duration: float, synth) -> Path:
    BUILD.mkdir(parents=True, exist_ok=True)
    path = BUILD / f"{name}.wav"
    rng = random.Random(f"rustchain-293:{name}:v1")
    frames = []
    total = int(RATE * duration)
    for i in range(total):
        t = i / RATE
        sample = clamp(synth(t, duration, rng))
        frames.append(struct.pack("<h", int(sample * 32767)))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))
    return path


def validator_pistol(t: float, d: float, rng: random.Random) -> float:
    # Rising charge followed by a crisp, short energy discharge.
    if t < 0.34:
        f = 280 + 1150 * (t / 0.34) ** 2
        sig = 0.27 * math.sin(2 * math.pi * f * t)
        sig += 0.10 * math.sin(2 * math.pi * 2.01 * f * t)
        return sig * env(t, 0.34, 0.02, 0.05)
    x = t - 0.34
    decay = math.exp(-9.0 * x)
    return decay * (0.63 * math.sin(2 * math.pi * 1040 * x) + 0.23 * noise(rng))


def forker_shotgun(t: float, d: float, rng: random.Random) -> float:
    # Mechanical pump, then two differentiated broadband blasts.
    pump = 0.0
    if t < 0.30:
        pump = 0.22 * math.sin(2 * math.pi * (95 + 130 * t) * t)
        pump += 0.18 * noise(rng)
        pump *= env(t, 0.30, 0.01, 0.05)
    blast = 0.0
    for start, pitch, amp in ((0.38, 120.0, 0.65), (0.52, 105.0, 0.55)):
        x = t - start
        if x >= 0:
            decay = math.exp(-13.0 * x)
            blast += amp * decay * (0.62 * noise(rng) + 0.38 * math.sin(2 * math.pi * pitch * x))
    return pump + blast


def hashcannon_railgun(t: float, d: float, rng: random.Random) -> float:
    # Computation-style wind-up that resolves into a high-energy beam snap.
    if t < 0.62:
        p = t / 0.62
        f = 70 + 1800 * p**3
        pulse = math.sin(2 * math.pi * f * t)
        quant = math.sin(2 * math.pi * (18 + 55 * p) * t)
        return (0.24 * pulse + 0.10 * quant) * (0.25 + 0.75 * p)
    x = t - 0.62
    beam = 0.67 * math.exp(-6 * x) * math.sin(2 * math.pi * (2350 - 900 * x) * x)
    crack = 0.21 * math.exp(-22 * x) * noise(rng)
    return beam + crack


def mempool_grenade(t: float, d: float, rng: random.Random) -> float:
    # Digital cluster ticks followed by a low, area-fill detonation.
    ticks = 0.0
    for start in (0.10, 0.20, 0.29, 0.37, 0.44):
        x = t - start
        if 0 <= x < 0.055:
            ticks += 0.25 * math.exp(-45 * x) * math.sin(2 * math.pi * (900 + 2500 * x) * x)
    x = t - 0.54
    boom = 0.0
    if x >= 0:
        decay = math.exp(-4.7 * x)
        boom = decay * (0.52 * math.sin(2 * math.pi * 62 * x) + 0.28 * noise(rng))
        boom += 0.18 * math.exp(-10 * x) * math.sin(2 * math.pi * 190 * x)
    return ticks + boom


def double_spend_smgs(t: float, d: float, rng: random.Random) -> float:
    # Alternating transaction-click bursts with a rapid-fire cadence.
    sig = 0.0
    cadence = 0.082
    shot = int(t / cadence)
    local = t - shot * cadence
    if shot < 12 and local < 0.060:
        left_right = 1.0 if shot % 2 == 0 else 0.86
        pitch = 620 if shot % 2 == 0 else 760
        decay = math.exp(-42 * local)
        sig += left_right * decay * (0.52 * math.sin(2 * math.pi * pitch * local) + 0.23 * noise(rng))
    # Quiet electronic bed prevents the sequence from sounding like generic gunfire.
    sig += 0.035 * math.sin(2 * math.pi * 43 * t)
    return sig


EFFECTS = {
    "validator_pistol": (1.00, validator_pistol, "energy charge + discharge"),
    "forker_shotgun": (1.25, forker_shotgun, "mechanical pump + dual blast"),
    "hashcannon_railgun": (1.45, hashcannon_railgun, "computation wind-up + beam"),
    "mempool_grenade": (1.75, mempool_grenade, "digital cluster + detonation"),
    "double_spend_smgs": (1.10, double_spend_smgs, "rapid alternating transaction clicks"),
}


def encode_ogg(wav_path: Path, ogg_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to encode OGG Vorbis")
    subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav_path), "-c:a", "libvorbis", "-q:a", "5", str(ogg_path)],
        check=True,
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "bounty": 293,
        "set": "RustChain Arena Weapon SFX",
        "license": "CC0-1.0",
        "generator": "generate.py",
        "sample_rate_hz": RATE,
        "channels": 1,
        "effects": [],
    }
    for name, (duration, fn, purpose) in EFFECTS.items():
        wav_path = write_wav(name, duration, fn)
        ogg_path = OUT / f"{name}.ogg"
        encode_ogg(wav_path, ogg_path)
        digest = hashlib.sha256(ogg_path.read_bytes()).hexdigest()
        manifest["effects"].append(
            {"file": str(ogg_path.relative_to(ROOT)), "purpose": purpose, "duration_seconds": duration, "sha256": digest}
        )
    (ROOT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"generated {len(EFFECTS)} original OGG effects in {OUT}")


if __name__ == "__main__":
    main()
