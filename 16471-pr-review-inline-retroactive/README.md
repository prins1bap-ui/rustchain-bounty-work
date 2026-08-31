# RustChain bounty #16471 finding: author-wide inline aggregation retroactively changes the first substantive reviewer

**Reporter:** `@prins1bap-ui`  
**RTC wallet:** `RTCc5449fe1b93385961152720c864c0f073dae5855`  
**Scope:** `scripts/pr_review_gate.py`  
**Current main checked:** `c5bcfb4dee714b4fbe12e574635f20ee784e0b4d`

## Summary

The PR-review bounty gate aggregates inline review comments by **author across the entire pull request**, then supplies that author-wide inline count to **every review** written by that author.

As a result, an early rubber-stamp review can be retroactively reclassified as substantive if that same reviewer later leaves an inline comment in a different, later review. Because reviews are then sorted by `submitted_at`, the earlier rubber-stamp can incorrectly become the `first substantive reviewer` and win the payout slot over someone who actually submitted the first substantive review.

This is a silent-success / wrong-effect path: the workflow can complete successfully, label or reject claims, and publish a confident adjudication while selecting the wrong reviewer.

## Current logic

The current gate builds one count per author:

```python
author_inline = {}
for c in inl:
    login = (c.get("user") or {}).get("login")
    if login:
        author_inline[login] = author_inline.get(login, 0) + 1

substantive = [r for r in rv if is_substantive_review(
    r, inline_count=author_inline.get(r["user"]["login"], 0)
)]
```

The inline-review API exposes `pull_request_review_id`, but that relationship is discarded here.

## Deterministic reproduction

Timeline:

1. **01:00 — reviewer-a:** submits `LGTM` with no inline comments. This is correctly non-substantive at the time.
2. **01:05 — reviewer-b:** submits a genuine substantive review naming a concrete bug and file/line.
3. **01:10 — reviewer-a:** submits a later review containing an inline comment.

With the current author-wide aggregation, reviewer-a now has `inline_count = 1`. That count is passed not only to the 01:10 review but also to reviewer-a's 01:00 `LGTM` review. `is_substantive_review()` therefore returns true immediately for the 01:00 review and the gate chooses reviewer-a as the first substantive reviewer.

If the inline comment is associated with its actual `pull_request_review_id`, reviewer-b is correctly selected.

Run:

```bash
python poc.py
```

Expected reproduction output:

```text
current_gate_first = reviewer-a
correct_first      = reviewer-b
REPRODUCED: later inline comment retroactively changes first-substantive reviewer
```

## Impact

A claimant can be incorrectly awarded or marked eligible even though another reviewer was genuinely first, while the legitimate claimant can be closed as not-first. No exception is raised and the workflow can remain green. The failure therefore matches #16471's target class: code achieves the wrong payout-adjudication effect without surfacing an error.

This report does not require any production interaction, wallet movement, or privileged access.

## Suggested fix

Count inline comments by `pull_request_review_id`, not by author:

```python
review_inline = {}
for c in inl:
    review_id = c.get("pull_request_review_id")
    if review_id is not None:
        review_inline[review_id] = review_inline.get(review_id, 0) + 1

substantive = [r for r in rv if is_substantive_review(
    r, inline_count=review_inline.get(r["id"], 0)
)]
```

A regression test should include an early rubber-stamp by A, an intervening substantive review by B, and a later inline review by A, and assert that B remains the first substantive reviewer.

## Proof

See `poc.py` in this directory. The proof is deterministic and uses no external services.

Submitted for maintainer confirmation under bounty #16471. No acceptance or payout is asserted until confirmed by the maintainer.