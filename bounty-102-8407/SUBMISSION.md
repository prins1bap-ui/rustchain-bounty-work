# RustChain #8407 — wallet config path documentation fix

## Target

- Issue: https://github.com/Scottcjn/Rustchain/issues/8407
- Upstream repository: `Scottcjn/Rustchain`
- Audited base: `aa584b344a766f6c0f8613ba7198d1cc7ffbae35`
- File: `docs/WALLET_SETUP.md`
- Upstream blob audited: `357ea36b89f6b8e69e82b28c54e98db19780df23`

## Defect

`docs/WALLET_SETUP.md` documents only `/opt/rustchain-miner/config.json` for a miner install, while the repository installers use `~/.rustchain/config.json`. A repo-installed user can therefore follow the wallet guide and look in the wrong location for `wallet_id`.

## Fix

The patch:

1. distinguishes the hosted `rustchain.org/install.sh` path from repository installer paths;
2. documents both `/opt/rustchain-miner/config.json` and `~/.rustchain/config.json` at first use;
3. updates backup guidance;
4. updates the `Where is my wallet stored?` FAQ;
5. updates wallet-recovery commands to check both paths.

No runtime code, API behavior, wallet state, keys, networking, or dependencies are changed.

## Collision check

Immediately before implementation, GitHub search returned zero pull requests referencing issue `#8407` in `Scottcjn/Rustchain`.

## Validation

- Patch targets the current `docs/WALLET_SETUP.md` content at the audited upstream base.
- Both paths are explained by installation method rather than presenting either as universally correct.
- Existing hosted-installer instructions remain valid.
- Documentation-only change; no production or wallet mutation required.

## Bounty route

Proposed under `Scottcjn/rustchain-bounties#102` Track A as a small but concrete onboarding/reliability improvement. Requested reward: 10 RTC, subject to maintainer assessment.

Wallet: `RTCc5449fe1b93385961152720c864c0f073dae5855`

AI assistance disclosure: ChatGPT prepared and validated the documentation patch from the cited current upstream source. No fabricated runtime evidence is claimed.
