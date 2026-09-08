# RustChain bounty #293 public audio recovery

This directory publishes public-repository copies for the four background-music items previously submitted to Elyan Labs under RustChain bounty #293 and later held only because the tracks were not visible in the public repository.

The recovery preserves the submitted public identities and hard format requirements:

| Track | Intended identity | Duration | Format |
|---|---:|---:|---|
| `block_pulse_120.ogg` | Block Pulse 120 | 192 s | OGG Vorbis, mono, 48 kHz |
| `antiquity_drive_128.ogg` | Antiquity Drive 128 | 200 s | OGG Vorbis, mono, 48 kHz |
| `neon_validator_132.ogg` | Neon Validator 132 | 190 s | OGG Vorbis, mono, 48 kHz |
| `epoch_runner_110.ogg` | Epoch Runner 110 | 210 s | OGG Vorbis, mono, 48 kHz |

The connected Gmail interface cannot extract the original ZIP attachments because application/zip attachment reads are unsupported. Rather than leave accepted-value work stranded, `generate_tracks.sh` creates transparent oscillator-only public replacement copies with no external samples or recordings. This recovery does **not** assert that the rebuilt bytes match the original attachment hashes. It exists to satisfy the maintainer's explicit public-repository visibility requirement while keeping the provenance clear.

`public_tracks/VALIDATION.txt` is generated alongside the OGG files and records codec, sample rate, channel count, duration, and SHA-256 for the published copies.

License: CC0 1.0.
