#!/usr/bin/env python3
"""Deterministic reproduction for RustChain bounty #16471.

Current pr_review_gate.py aggregates inline review comments by author across the
entire PR, then supplies that author-wide count to every review by the author.
This can retroactively turn an earlier rubber-stamp into a substantive review
when the same author leaves an inline comment in a later review.

No network access, credentials, wallets, or production state are used.
"""


def is_substantive_review(review, inline_count=0):
    """Minimal reproduction of the relevant current gate behavior."""
    if inline_count and inline_count > 0:
        return True
    body = (review.get("body") or "").strip()
    if not body:
        return False
    substantive_markers = ("bug", "issue", "risk", "line ", ".py")
    if any(marker in body.lower() for marker in substantive_markers):
        return True
    if len(body) >= 80:
        return True
    return False


reviews = [
    {
        "id": 101,
        "submitted_at": "2026-08-31T01:00:00Z",
        "user": {"login": "reviewer-a"},
        "body": "LGTM",
    },
    {
        "id": 202,
        "submitted_at": "2026-08-31T01:05:00Z",
        "user": {"login": "reviewer-b"},
        "body": "Bug: parser.py line 42 accepts malformed input and should reject it.",
    },
    {
        "id": 303,
        "submitted_at": "2026-08-31T01:10:00Z",
        "user": {"login": "reviewer-a"},
        "body": "Follow-up review",
    },
]

# The only inline comment belongs to reviewer-a's LATER review (id=303).
inline_comments = [
    {
        "pull_request_review_id": 303,
        "user": {"login": "reviewer-a"},
        "body": "Concrete line-level follow-up.",
    }
]

reviews.sort(key=lambda r: r["submitted_at"])

# Current gate logic: aggregate by AUTHOR, losing which review owned the inline.
author_inline = {}
for comment in inline_comments:
    login = (comment.get("user") or {}).get("login")
    if login:
        author_inline[login] = author_inline.get(login, 0) + 1

current_substantive = [
    review
    for review in reviews
    if is_substantive_review(
        review,
        inline_count=author_inline.get(review["user"]["login"], 0),
    )
]
current_first = current_substantive[0]["user"]["login"]

# Correct association: bind each inline comment to its pull_request_review_id.
review_inline = {}
for comment in inline_comments:
    review_id = comment.get("pull_request_review_id")
    if review_id is not None:
        review_inline[review_id] = review_inline.get(review_id, 0) + 1

correct_substantive = [
    review
    for review in reviews
    if is_substantive_review(
        review,
        inline_count=review_inline.get(review["id"], 0),
    )
]
correct_first = correct_substantive[0]["user"]["login"]

print("current_gate_first =", current_first)
print("correct_first      =", correct_first)

assert current_first == "reviewer-a"
assert correct_first == "reviewer-b"
assert current_first != correct_first

print("REPRODUCED: later inline comment retroactively changes first-substantive reviewer")
