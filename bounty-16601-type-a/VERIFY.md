# Validation

Validated in GitHub Actions on 2026-09-02.

```text
script_words=768
voiceover_sections=7
voiceover_duration_seconds=338.16
visuals=10 at 1920x1080
thumbnails=3 at 1280x720
source_lock_present= True
PASS
```

## Reproduction

```bash
python scripts/generate_assets.py
python scripts/synthesize.py
python scripts/verify.py
```

Narration uses eSpeak at 145 words/minute as documented in `voiceover/ENGINE.md`.
