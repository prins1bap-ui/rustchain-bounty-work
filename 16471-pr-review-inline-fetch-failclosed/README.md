# RustChain bounty #16471 finding: failed inline-comment read is treated as authoritative zero and can reject the rightful reviewer

**Reporter:** `@prins1bap-ui`  
**RTC wallet:** `RTCc5449fe1b93385961152720c864c0f073dae5855`  
**Scope:** `scripts/pr_review_gate.py`  
**Current main checked:** `c5bcfb4dee714b4fbe12e574635f20ee784e0b4d`

## Summary

The PR-review bounty gate uses inline review comments as a positive signal for whether a review is substantive. However, the inline-comment API call is non-strict:

```python
inl = api(f"/repos/{target}/pulls/{pr}/comments?per_page=100") or []
```

For failed GET requests, `api()` returns `None`. The `or []` therefore converts an API/auth/rate-limit/HTTP read failure into an authoritative claim that the PR has **zero inline review comments**.

The gate then continues its money decision with incomplete evidence. A reviewer whose substantive work is carried by line-level comments can be silently removed from consideration, causing a later reviewer to be selected as first substantive. The rightful claimant can then be closed as not-first while the workflow remains green.

## Deterministic reproduction

Timeline:

1. **01:00 — claimant-a:** submits a short summary (`See inline comment.`) plus a real line-level inline finding. Under a healthy read, the inline comment makes this review substantive.
2. **01:05 — reviewer-b:** submits a later substantive body review.
3. The gate successfully reads the review list but the separate `/pulls/<pr>/comments` GET fails.
4. `api()` returns `None`; `or []` turns that into zero inline comments.
5. claimant-a's review is now treated as non-substantive, reviewer-b becomes `first`, and claimant-a's claim can be closed as not-first.

Run:

```bash
python poc.py
```

Expected output:

```text
healthy_first      = claimant-a
after_fetch_failure= reviewer-b
REPRODUCED: failed inline-comment read becomes empty evidence and changes payout adjudication
```

## Why this is a #16471 silent-success defect

The gate is making a payout-eligibility decision using a read that failed. The failed read does not force `needs-human`, a retry, or a non-zero exit. Instead, the missing evidence is silently rewritten as `[]`, after which the normal adjudication path can close a valid claim and apply terminal labels/comments.

This is distinct from the previously reported contributor-cap lookup failure: that defect concerns the org-wide cap and approval past a ceiling; this defect concerns a separate PR inline-comment read and can falsely reject the actual first substantive reviewer.

## Suggested fix

Treat the inline-comment read as strict whenever it feeds first-reviewer adjudication:

```python
try:
    inl = api(
        f"/repos/{target}/pulls/{pr}/comments?per_page=100",
        strict=True,
    )
except ApiError as e:
    _unresolved(
        "Gate: could not read inline review comments, so first-reviewer "
        "eligibility cannot be decided safely. Holding for retry/human review.",
        quiet,
    )
    return
```

Also distinguish an actual successful empty list (`[]`) from a failed read (`None`). A regression test should simulate a successful review-list read plus a failed inline-comment read and assert that the claim is not approved or closed.

## Proof

See `poc.py` in this directory. It uses no external services, credentials, wallets, or production state.

Submitted for maintainer confirmation under bounty #16471. No acceptance or payout is asserted until confirmed by the maintainer.