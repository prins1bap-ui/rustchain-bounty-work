# RustChain Bounty Verification Bot — #747

A **read-only, human-in-the-loop** verifier for RustChain bounty claims. It implements the five milestones listed in `Scottcjn/rustchain-bounties#747` without executing payment or moving funds.

## Milestones

- **30 RTC basis:** verifies whether a claimant follows `@Scottcjn`, paginates the claimant's starred repositories, and counts `Scottcjn/*` stars.
- **+10 RTC basis:** checks claimed wallet / `miner_id` existence using the configured RustChain node balance endpoint.
- **+10 RTC basis:** verifies a proof URL is live, using HEAD with GET fallback.
- **+10 RTC basis:** counts words for Dev.to / Medium proof URLs and marks 500+ words as passing.
- **+15 RTC basis:** scans prior issue comments for claimant/wallet-specific payout markers (`paid`, `queued`, `pending_id`, `txid`, etc.).

The output is a **suggested payout basis only**. Maintainers make the final decision. The verifier has no payment, wallet-write, transfer, signing, escrow, settlement, or payout code.

## Automatic issue-comment mode

`issue_comment_handler.py` is the deployment adapter requested by #747. It:

1. receives GitHub `issue_comment.created` events,
2. ignores non-claim comments and bot-generated output,
3. identifies claim-like comments containing markers such as `Claiming`, `Wallet:`, `miner_id:`, `Submitted`, or `/claim`,
4. fetches the issue's prior comments for duplicate-payment evidence,
5. runs the read-only verifier,
6. posts a markdown verification table back to the issue, and
7. embeds the source comment ID so an Actions retry does not post the same verification twice.

The project-level `.github/workflows/verify.yml` is a deployable workflow template. Because GitHub only fires `issue_comment` workflows for the repository containing the workflow, copy the project into its standalone deployment repository (or copy this workflow and the verifier files to the target bounty repository root) before enabling automatic comment handling. The workflow grants only `contents: read` and `issues: write`; the latter is used solely to post verification comments.

## Local QA

```bash
python -m unittest discover -s tests -v
python verifier.py --user example --claim-text 'Wallet: example-wallet Proof: https://dev.to/example/post'
```

The repository-root CI workflow runs the complete offline unit-test suite for this project on every relevant push/PR. The event-adapter tests specifically cover claim filtering, bot-loop prevention, posting, and retry idempotency.

## Safety / operational properties

- zero third-party Python dependencies
- URL schemes restricted to HTTP/HTTPS
- finite GitHub pagination in the verifier
- paginated issue-history retrieval in the event adapter
- configurable node URL via `RUSTCHAIN_NODE_URL`
- explicit unknown state (`⚪`) instead of treating network failures as passes
- no secrets printed by the verifier
- idempotency marker prevents duplicate verification comments on workflow retry
- no payment execution
- human approval remains mandatory

Initial verifier QA: 9/9 tests passed before publication. Event-adapter QA: 4/4 focused tests passed before publication of the adapter.

AI assistance used in implementation. Claimant: `@prins1bap-ui`.
