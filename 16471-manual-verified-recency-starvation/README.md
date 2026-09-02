# RustChain #16471 finding: trusted comment-only verification still ages out of the payout candidate set

Current source: `scripts/bounty_payout.py`.

The payout runner explicitly supports two authorization routes: the `bounty-eligible` label **or** a trusted-author comment containing `Verified eligible`.

Candidate construction, however, is asymmetric:
- label-authorized claims are fetched by `--label bounty-eligible --limit 1000`;
- every non-label candidate must come from a generic `--limit 400` recent-open-issue sweep.

The trusted comment authorization is not checked until *after* those two candidate lists are built.

Concrete silent-success path:

1. A maintainer manually verifies an old review claim by posting the supported `Verified eligible` comment but does not add `bounty-eligible`.
2. The claim has no payout destination yet, or otherwise remains open while more issues are created.
3. Once it is older than the newest 400 open issues, it is absent from both candidate passes: it has no label, and it is outside the recent 400.
4. Adding a wallet later does not help. The payout script never loads the issue, so it never reaches the trusted-comment eligibility check.
5. Scheduled payout runs continue green and the manually verified claim can remain unpaid indefinitely.

This is the residual half of the earlier recency bug: the label-based route was repaired with a dedicated label sweep, but the explicitly supported trusted-comment route is still recency-bound.

Suggested remediation: enumerate trusted comment-only eligible claims from durable state rather than a recent-open window, preferably by converting manual verification into the same `bounty-eligible` label or persisting a dedicated eligibility label when the trusted comment is made.

`repro.py` models an old comment-only eligible issue outside the newest 400 and shows that the later eligibility check is unreachable.
