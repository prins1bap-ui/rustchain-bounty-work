# RustChain #8408 / #102 Track A — Fully Offline Linux Miner Preflight

## Target

- Bounty: `Scottcjn/rustchain-bounties#102` — Track A, miner UX / new capability
- Bug: `Scottcjn/Rustchain#8408`
- Audited upstream base: `aa584b344a766f6c0f8613ba7198d1cc7ffbae35`
- Claimant: `@prins1bap-ui`
- RTC wallet: `RTCc5449fe1b93385961152720c864c0f073dae5855`

## Problem

The Linux miner's `--dry-run` path is state-safe but not network-silent. It performs two link-local cloud-metadata probes during anti-emulation and then a node `/health` request through the normal retry path. That leaves isolated CI/sandboxes with no zero-network preflight.

## Fix

Add an explicit `--offline` mode for dry-run:

```bash
python miners/linux/rustchain_linux_miner.py \
  --dry-run --offline --show-payload --verbose \
  --wallet RTC...
```

The patch:

- retains local hardware discovery;
- retains local DMI/proc/WMI/systemd anti-emulation checks;
- skips only the network-backed cloud-metadata probes;
- skips the node `/health` request entirely;
- preserves non-persistent/ephemeral dry-run key behavior;
- rejects `--offline` unless paired with `--dry-run`;
- leaves normal mining and ordinary online dry-run behavior unchanged;
- records `network_metadata_probes_skipped: true` in anti-emulation evidence.

## Upstream files changed

1. `miners/linux/rustchain_linux_miner.py`
2. `miners/linux/fingerprint_checks.py`
3. `docs/sprint/miner-setup-guide.md`
4. `tests/test_linux_miner_offline_dry_run.py` (new)

## Regression coverage

The proposed tests prove:

- `--offline` fails closed without `--dry-run`;
- CLI wiring passes `offline=True` while retaining `persist_key=False`;
- offline dry-run cannot invoke the node `_get()` health path;
- offline anti-emulation cannot invoke `urllib.request.urlopen`;
- the result explicitly records that metadata probes were intentionally skipped.

## Validation

Package QA before publication:

```text
pytest test_patch_package.py
3 passed
```

The proposed upstream validation after applying the patch is:

```bash
python -m pytest -q \
  tests/test_linux_miner_identity.py \
  tests/test_linux_miner_offline_dry_run.py

python -m py_compile \
  miners/linux/rustchain_linux_miner.py \
  miners/linux/fingerprint_checks.py \
  tests/test_linux_miner_offline_dry_run.py

git diff --check
```

## Submission route

The connected GitHub App cannot write to `Scottcjn/Rustchain`, and no writable `prins1bap-ui/Rustchain` fork is exposed to the integration. RustChain's official bounty guide explicitly permits publishing a patch in a contributor-controlled repository and emailing `sophia.eagent@gmail.com`; maintainers can file the PR on the contributor's behalf.

AI assistance disclosed. No production endpoint was mutated and no RTC was spent.
