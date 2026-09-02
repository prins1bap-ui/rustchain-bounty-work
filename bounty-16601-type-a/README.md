# RustChain #16601 — Type A Full Production Kit

Publication-ready YouTube production package for bounty #16601.

**Pitch:** A source-locked, roughly five-minute explainer showing why RustChain’s Proof-of-Antiquity protocol can assign a 2003 PowerBook G4 higher reward weight than modern x86 hardware, how the documented six-check hardware fingerprint works, and why those multipliers must not be confused with compute speed or guaranteed profit.

## Contents
- `script.md` — full narration script, timed by section
- `voiceover/` — seven narration WAV files; generated locally with eSpeak, 145 words/minute
- `visuals/` — ten original 1920×1080 explanatory frames
- `assembly.md` — edit map pairing every section with visuals
- `thumbnails/` — three original 1280×720 thumbnail options
- `metadata.md` — titles, description, tags, chapters
- `SOURCES.md` — factual claim → public source mapping
- `VERIFY.md` — validation results and reproducibility checklist
- `scripts/generate_assets.py` — deterministic visual generator
- `scripts/verify.py` — package QA

## Source lock
All factual technical claims are sourced to `Scottcjn/Rustchain@5a9d6a8a190008446d4f6c5ed2358bde532ba325` and mapped in `SOURCES.md`.

## Rights
All text, generated diagrams, thumbnails, and narration files in this package were created for this bounty submission. Elyan Labs may publish them with permanent attribution to **@prins1bap-ui**, consistent with bounty #16601.

## AI disclosure
This package was produced with AI assistance and programmatic asset generation, then constrained to source-backed factual claims. No third-party stock footage, music, or copied narration is included.