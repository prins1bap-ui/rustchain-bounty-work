# RustChain bounty #16471 finding: later substantive review is rejected using the claimant's earlier review-body length

**Reporter:** `@prins1bap-ui`  
**RTC wallet:** `RTCc5449fe1b93385961152720c864c0f073dae5855`  
**Scope:** `scripts/pr_review_gate.py`  
**Current main checked:** `c5bcfb4dee714b4fbe12e574635f20ee784e0b4d`

## Summary

The gate first identifies the first substantive review from the complete ordered review list. But after confirming the claimant is that first substantive reviewer, it performs a second summary-length check using the claimant's **first review body**, not the review that was actually classified as substantive:

```python
first = substantive[0]["user"]["login"] if substantive else None
body_len = next(
    (len(r.get("body") or "") for r in rv if r["user"]["login"] == author),
    0,
)
inline = author_inline.get(author, 0)

if first != author:
    close(...)
    return
if inline == 0 and body_len < 120:
    close(... "no substantive summary" ...)
    return
```

If the claimant first left a short rubber-stamp and later submitted the first genuine substantive review, `substantive[0]` correctly points to the later review, but `body_len` still comes from the earlier rubber-stamp. The gate then closes the claim for lacking a substantive summary even though its own preceding classification says the claimant has the first substantive review.

## Deterministic reproduction

Timeline:

1. **01:00 — claimant-a:** `LGTM` (4 chars, non-substantive, no inline comment).
2. **01:05 — claimant-a:** a 120+ character review with a concrete parser/file/line correctness finding.
3. No other reviewer has a substantive review before it.

The gate's substantive filter correctly selects claimant-a's 01:05 review and sets `first = claimant-a`.

Then:

- current `body_len` = 4, because `next(...)` returns claimant-a's first review (`LGTM`)
- actual substantive-review body length = 120+
- current gate enters the rejection branch and closes the claim

Run:

```bash
python poc.py
```

Expected output includes:

```text
first_substantive  = claimant-a
current_body_len   = 4
correct_body_len   = <120+>
current_closes     = True
correct_closes     = False
REPRODUCED: gate finds later substantive review, then closes claimant using earlier rubber-stamp length
```

## Impact

A contributor who improves an earlier shallow review by submitting a later genuine substantive review can be denied even when they are the first substantive reviewer according to the gate's own classification logic. The gate closes the issue and publishes a confident rejection; no error is surfaced.

That is a direct #16471 wrong-effect path: adjudication completes successfully but produces a result inconsistent with the evidence already computed inside the same run.

## Suggested fix

Track the actual review object that establishes first-substantive status and validate that review's body/inline evidence, rather than calling `next(...)` across every review by the claimant. Better still, have `is_substantive_review()` return or preserve the qualifying evidence so the same review is used consistently throughout adjudication.

A regression should include an early short rubber-stamp followed by a later 120+ character substantive review from the same claimant and assert that the later review is not rejected because of the earlier body's length.

## Proof

See `poc.py` in this directory. No external services, credentials, wallets, or production state are used.

Submitted for maintainer confirmation under bounty #16471. No acceptance or payout is asserted until confirmed by the maintainer.