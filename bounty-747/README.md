# RustChain Bounty #747 — Verification Bot

Verification-only implementation for Scottcjn/rustchain-bounties#747.

## Scope

- Parse bounty claim comments.
- Verify whether a claimant follows the configured GitHub account.
- Count stars across configured-owner repositories with pagination.
- Check whether an RTC wallet/miner ID resolves on a configured RustChain node.
- Verify article URLs against an allowlist and estimate visible article word count.
- Detect prior paid/accepted claims from issue history.
- Produce a machine-readable and Markdown verification report.

## Safety boundary

This project **never executes RTC payments or transfers**. It only gathers evidence and produces a suggested verification result for human review.

## Configuration

Environment variables:

- `GITHUB_TOKEN` — GitHub API token.
- `RUSTCHAIN_NODE_URL` — node base URL, e.g. `https://50.28.86.131`.
- `TARGET_OWNER` — account whose follow/star status is verified (default `Scottcjn`).

## Run

```bash
python -m bounty_verifier.cli --repo Scottcjn/rustchain-bounties --issue 747 --comment-id 123456
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Design notes

The verifier fails closed: network/API errors become `unknown` rather than a passing result. Duplicate detection does not infer payment from arbitrary numbers; it requires explicit payout/acceptance language in prior comments. URL checks reject non-HTTP(S), localhost/private-network targets, redirects to disallowed targets, and unsupported article hosts.

RTC wallet for bounty review: `RTCc5449fe1b93385961152720c864c0f073dae5855`.
