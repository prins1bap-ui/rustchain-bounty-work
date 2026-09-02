# Sources and contract snapshot

## Authoritative bounty

- https://github.com/Scottcjn/rustchain-bounties/issues/685
- Rechecked on 2026-09-02.
- State observed: open.
- Tier 1 observed: SDK/Client Library — 50 RTC each.
- Explicit target observed: Rust client crate.
- Primary node URL in the bounty: `https://50.28.86.131`.

## Current public server contract

Authoritative implementation reviewed on current `Scottcjn/Rustchain` main:

- https://github.com/Scottcjn/Rustchain/blob/main/rip302_agent_economy.py
- Blob SHA observed during reconciliation: `d2aced1ea52280af369d717a7fbcf462c64ff1e6`

The implementation currently defines:

1. `POST /agent/jobs` — requires `poster_wallet`, title >= 5 chars, description >= 20 chars, a supported category, and `reward_rtc` from 0.01 through 10000; optional TTL and tags are supported.
2. `GET /agent/jobs` — query fields include category, status, limit, offset, and `min_reward`.
3. `GET /agent/jobs/<id>` — job detail + activity/ratings.
4. `POST /agent/jobs/<id>/claim` — `worker_wallet`.
5. `POST /agent/jobs/<id>/deliver` — `worker_wallet`, at least one of `deliverable_url` or `result_summary`, plus optional `deliverable_hash`.
6. `POST /agent/jobs/<id>/accept` — `poster_wallet` plus optional rating.
7. `POST /agent/jobs/<id>/dispute` — `poster_wallet` + reason.
8. `POST /agent/jobs/<id>/cancel` — `poster_wallet`.
9. `GET /agent/reputation/<wallet>` — reputation.
10. `GET /agent/stats` — marketplace stats.

This current-main review supersedes the crate's original assumption that accept/dispute/cancel bodies were undocumented. The SDK has been updated to typed request models and stricter preflight validation that mirrors the public implementation where practical.

## Submission route

- https://github.com/Scottcjn/rustchain-bounties/blob/main/docs/HOW_TO_SUBMIT_A_BOUNTY.md
- The project has previously documented email fallback for GitHub App `403 Resource not accessible by integration` cases.
- Existing #685 delivery correspondence was sent to `sophia.eagent@gmail.com`; duplicate Tier 1 emails refer to one underlying Rust-client claim, not multiple economic claims.

## Safety boundary

No live POST request or fund-moving action is used to build or test this crate. Local mock-server tests exercise mutation routes without touching RustChain state, escrow, signatures, or balances.
