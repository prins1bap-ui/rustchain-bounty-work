# RustChain Arena Announcer Voice Lines — Bounty #293

Original synthesized announcer package targeting the still-open announcer / kill-streak category in `Scottcjn/rustchain-bounties#293`.

## Included lines

### Kill streaks
- `double_spend.ogg` — “Double spend!”
- `triple_fork.ogg` — “Triple fork!”
- `consensus_reached.ogg` — “CONSENSUS REACHED!”

### Style ranks
- `calculating.ogg` — “Calculating...”
- `building_momentum.ogg` — “Building momentum!”
- `singularity.ogg` — “SINGULARITY!”

### Match events
- `block_confirmed.ogg` — “Block confirmed”
- `chain_reorganization.ogg` — “Chain reorganization!”
- `fifty_one_attack_detected.ogg` — “51% attack detected!”

## Production method

The voice is synthesized locally with eSpeak NG and transformed with ffmpeg using filtering, compression, normalization, and a restrained arena echo. No human recordings, stock audio, music, or external samples are used.

## Format and QA

- OGG Vorbis
- 48 kHz
- mono
- nine required lines
- deterministic command parameters
- SHA-256 manifest
- CI validates codec, sample rate, channels, duration bounds, file presence, and hashes

## Rebuild

```bash
sudo apt-get install espeak-ng ffmpeg
python3 293-xonotic-announcer/generate.py
python3 293-xonotic-announcer/validate.py
```

## License

The package-specific generator, documentation, and generated outputs are dedicated under CC0-1.0 to the extent legally possible. eSpeak NG is used only as the local synthesis engine; no eSpeak source code or voice data files are redistributed in this directory. See `LICENSE-CC0.txt`.

## Claim boundary

This is a public deliverable for maintainer review only. It does not assert merge, acceptance, queued payout, pending transfer, or received RTC without authoritative maintainer evidence.
