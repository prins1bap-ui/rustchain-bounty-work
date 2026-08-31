# RustChain Arena Weapon SFX — Bounty #293

Original procedural audio set for `Scottcjn/rustchain-bounties#293`.

## Deliverable

Five distinct weapon/event effects matching the bounty's named set:

| File | Intended game cue |
|---|---|
| `sounds/weapons/validator_pistol.ogg` | energy charge + discharge |
| `sounds/weapons/forker_shotgun.ogg` | mechanical pump + dual blast |
| `sounds/weapons/hashcannon_railgun.ogg` | computation wind-up + high-energy beam |
| `sounds/weapons/mempool_grenade.ogg` | digital cluster + area-fill detonation |
| `sounds/weapons/double_spend_smgs.ogg` | rapid alternating transaction clicks |

All source PCM is generated deterministically by `generate.py` from mathematical waveforms and seeded synthetic noise. There are **no external samples, recordings, stock assets, or third-party media**.

## Format

- OGG Vorbis
- 48,000 Hz
- mono
- deterministic source generator included
- SHA-256 hashes recorded in `MANIFEST.json`

## Rebuild

```bash
python3 293-xonotic-weapon-sfx/generate.py
python3 293-xonotic-weapon-sfx/validate.py
```

`ffmpeg` and `ffprobe` are required. The repository workflow rebuilds and validates the package on GitHub Actions and commits the generated OGG files so reviewers can listen without running the generator.

## Integration

The files are intentionally named by weapon to make the eventual engine mapping obvious. When upstreamed, they can be copied into the Xonotic RustChain Arena sound package and referenced from the corresponding QuakeC weapon events.

## License

The generator, documentation, and generated audio files in this directory are dedicated to the public domain under **CC0-1.0**. See `LICENSE-CC0.txt`.

## Claim boundary

This directory is a public deliverable for maintainer review. It does not assert merge, acceptance, queued payout, pending transaction, or received RTC until the maintainer provides authoritative evidence.
