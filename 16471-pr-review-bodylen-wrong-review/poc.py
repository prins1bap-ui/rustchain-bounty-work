#!/usr/bin/env python3
"""Deterministic reproduction for RustChain bounty #16471.

Current pr_review_gate.py identifies the first substantive review correctly from
all reviews, but its later summary-length gate uses `next(...)` over *all* reviews
by the claimant. That returns the claimant's earliest review body, not the body
of the substantive review that established eligibility.

No network, credentials, wallets, or production state are used.
"""


def is_substantive_review(review, inline_count=0):
    if inline_count and inline_count > 0:
        return True
    body = (review.get("body") or "").strip()
    if not body:
        return False
    if any(marker in body.lower() for marker in ("bug", "issue", "risk", "line ", ".py")):
        return True
    if len(body) >= 80:
        return True
    return False


author = "claimant-a"
reviews = [
    {
        "id": 101,
        "submitted_at": "2026-08-31T01:00:00Z",
        "user": {"login": author},
        "body": "LGTM",
    },
    {
        "id": 202,
        "submitted_at": "2026-08-31T01:05:00Z",
        "user": {"login": author},
        "body": (
            "The parser has a concrete correctness issue in parser.py line 42: "
            "malformed integer input is silently accepted and coerced. Please "
            "reject the invalid value and add a regression test for the failure path."
        ),
    },
]
reviews.sort(key=lambda r: r["submitted_at"])

author_inline = {author: 0}
substantive = [
    r for r in reviews
    if is_substantive_review(r, inline_count=author_inline.get(r["user"]["login"], 0))
]
first = substantive[0]["user"]["login"] if substantive else None

# Current source logic.
body_len_current = next(
    (len(r.get("body") or "") for r in reviews if r["user"]["login"] == author),
    0,
)
inline = author_inline.get(author, 0)
current_closes = first == author and inline == 0 and body_len_current < 120

# Correctly measure the substantive review that established the author's slot.
author_substantive = next(
    (r for r in substantive if r["user"]["login"] == author),
    None,
)
body_len_correct = len((author_substantive or {}).get("body") or "")
correct_closes = first == author and inline == 0 and body_len_correct < 120

print("first_substantive  =", first)
print("current_body_len   =", body_len_current)
print("correct_body_len   =", body_len_correct)
print("current_closes     =", current_closes)
print("correct_closes     =", correct_closes)

assert first == author
assert body_len_current == len("LGTM")
assert body_len_correct >= 120
assert current_closes is True
assert correct_closes is False

print("REPRODUCED: gate finds later substantive review, then closes claimant using earlier rubber-stamp length")
