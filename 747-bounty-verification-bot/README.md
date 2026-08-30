# RustChain Bounty Verification Bot — #747

A **read-only, human-in-the-loop** verifier for RustChain bounty claims. It implements the five milestones listed in `Scottcjn/rustchain-bounties#747` without executing payment or moving funds.

## Milestones

- **30 RTC basis:** verifies whether a claimant follows `@Scottcjn`, paginates the claimant's starred repositories, and counts `Scottcjn/*` stars.
- **+10 RTC basis:** checks claimed wallet / `miner_id` existence using the configured RustChain node balance endpoint.
- **+10 RTC basis:** verifies a proof URL is live, using HEAD with GET fallback.
- **+10 RTC basis:** counts words for Dev.to / Medium proof URLs and marks 500+ words as passing.
- **+15 RTC basis:** scans supplied prior issue comments for claimant/wallet-specific payout markers (`paid`, `queued`, `pending_id`, `txid`, etc.).

The output is a **suggested payout basis only**. Maintainers make the final decision. The verifier has no payment, wallet-write, transfer, signing, or escrow code.

## Local QA

```bash
python -m unittest discover -s tests -v
python verifier.py --user example --claim-text 'Wallet: example-wallet Proof: https://dev.to/example/post'
```

## GitHub Action

The included workflow runs tests on push/PR and supports manual verification via `workflow_dispatch`. It deliberately does **not** auto-pay. A deployment can wire its markdown output to an `issue_comment` handler using the repository's normal `GITHUB_TOKEN` permissions.

## Safety / operational properties

- zero third-party Python dependencies
- URL schemes restricted to HTTP/HTTPS
- finite GitHub pagination (`max_pages`)
- configurable node URL via `RUSTCHAIN_NODE_URL`
- explicit unknown state (`⚪`) instead of treating network failures as passes
- no secrets printed by the verifier
- no payment execution

QA: 9/9 tests passing locally before publication.

AI assistance used in implementation. Claimant: `@prins1bap-ui`.
