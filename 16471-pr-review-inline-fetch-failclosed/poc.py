#!/usr/bin/env python3
"""Deterministic reproduction for RustChain bounty #16471.

Current pr_review_gate.py does:
    inl = api(.../pulls/<pr>/comments?per_page=100) or []

For GET failures, api() returns None unless strict=True. The `or []` therefore
turns an unavailable inline-review-comment read into authoritative evidence that
there were zero inline comments, even though inline comments are a positive
signal used to decide who was first substantive reviewer.

No network, credentials, wallets, or production state are used.
"""


def is_substantive_review(review, inline_count=0):
    if inline_count and inline_count > 0:
        return True
    body = (review.get("body") or "").strip()
    if not body:
        return False
    markers = ("bug", "issue", "risk", "line ", ".py")
    if any(marker in body.lower() for marker in markers):
        return True
    if len(body) >= 80:
        return True
    return False


reviews = [
    {
        "id": 101,
        "submitted_at": "2026-08-31T01:00:00Z",
        "user": {"login": "claimant-a"},
        "body": "See inline comment.",
    },
    {
        "id": 202,
        "submitted_at": "2026-08-31T01:05:00Z",
        "user": {"login": "reviewer-b"},
        "body": "Bug: parser.py line 42 accepts malformed input and should reject it.",
    },
]
reviews.sort(key=lambda r: r["submitted_at"])

# Ground truth: GitHub has a line-level comment attached to claimant-a's review.
real_inline_comments = [
    {
        "pull_request_review_id": 101,
        "user": {"login": "claimant-a"},
        "body": "Line-level finding on parser.py.",
    }
]

# Healthy read.
author_inline_healthy = {}
for c in real_inline_comments:
    login = (c.get("user") or {}).get("login")
    if login:
        author_inline_healthy[login] = author_inline_healthy.get(login, 0) + 1

healthy_substantive = [
    r for r in reviews
    if is_substantive_review(r, author_inline_healthy.get(r["user"]["login"], 0))
]
healthy_first = healthy_substantive[0]["user"]["login"]

# Simulate current api() behavior on an HTTP GET failure: return None.
api_result_on_failure = None

# Current gate then executes `inl = api(...) or []`.
inl = api_result_on_failure or []
author_inline_failed = {}
for c in inl:
    login = (c.get("user") or {}).get("login")
    if login:
        author_inline_failed[login] = author_inline_failed.get(login, 0) + 1

failed_substantive = [
    r for r in reviews
    if is_substantive_review(r, author_inline_failed.get(r["user"]["login"], 0))
]
failed_first = failed_substantive[0]["user"]["login"] if failed_substantive else None

print("healthy_first      =", healthy_first)
print("after_fetch_failure=", failed_first)

assert healthy_first == "claimant-a"
assert failed_first == "reviewer-b"
assert healthy_first != failed_first

print("REPRODUCED: failed inline-comment read becomes empty evidence and changes payout adjudication")
