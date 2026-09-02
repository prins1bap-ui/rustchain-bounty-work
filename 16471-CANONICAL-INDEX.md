# RustChain #16471 — @prins1bap-ui canonical audit index

Status: **submitted for maintainer adjudication; no acceptance or RTC payment is asserted here.**

Bounty: `Scottcjn/rustchain-bounties#16471` — payout-pipeline silent-success audit.

Claimant: `@prins1bap-ui`  
RTC wallet: `RTCc5449fe1b93385961152720c864c0f073dae5855`

Because direct issue-comment writes from the connected GitHub integration return `403 Resource not accessible by integration`, the detailed reports were sent through the established email fallback. This page is only a canonical review index. It does not create additional claims or request duplicate credit.

## Submitted findings

1. `docstring_gate.py` masks `gh pr diff` failure.
2. An untrusted comment can suppress an unpaid eligible claim.
3. Docstring gate promises retry, then excludes the claim.
4. PR-review contributor-cap search failure fails open.
5. `MAX_PER_RUN` counts successful claims rather than aggregate RTC.
6. Backfill silently ignores failed issue enumeration.
7. A later inline comment can retroactively rewrite the first substantive reviewer.
8. Failed inline-comment API read can silently change the first-reviewer payout decision.
9. Gate finds a later substantive review but rejects using the earlier `LGTM` body length.
10. Backfill silently omits older claims beyond its 1,000-issue window.
11. PR-review gate silently ignores reviews after page 1.
12. Malformed payout-inventory JSON is silently converted to zero candidates.
13. Review-comment page-2 evidence is silently erased.
14. Weekly docstring cap uses issue creation date instead of verification-marker date.
15. Backfill converts malformed/truncated issue-list JSON into a successful empty sweep.
16. Scheduled docstring sweep can permanently starve search page 2 behind 60 persistent `awaiting-merge` claims. Repro: [`16471-docstring-sweep-page1-starvation/`](./16471-docstring-sweep-page1-starvation/)
17. Weekly docstring cap trusts the first payout marker from any commenter, so a pre-seeded zero marker can erase a later trusted grant from cap accounting. Repro: [`16471-docstring-cap-untrusted-first-marker/`](./16471-docstring-cap-untrusted-first-marker/)
18. Per-issue workflow concurrency makes the weekly docstring cap a non-atomic read-then-approve check; simultaneous claims by one contributor can both pass and overrun the ceiling. Repro: [`16471-docstring-weekly-cap-concurrency-race/`](./16471-docstring-weekly-cap-concurrency-race/)
19. Trusted comment-only `Verified eligible` claims remain bound to the generic recent-400 candidate sweep and can silently age out of payout discovery. Repro: [`16471-manual-verified-recency-starvation/`](./16471-manual-verified-recency-starvation/)

## Accounting rule

Each item remains **SUBMITTED** until the maintainer confirms that it is a qualifying, non-duplicate defect under #16471. A merged fix, email delivery, repository commit, or reproduction is not counted as acceptance or payment. RTC is counted as received only after verifiable settlement to the wallet above.
