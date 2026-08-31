#!/usr/bin/env python3
"""Deterministic model of RustChain #16471 backfill enumeration truncation.

Current scripts/pr_review_gate_backfill.py asks:
    gh issue list --state open --limit 1000 --json number,title,labels
then sorts only the returned review claims by issue number (oldest first).

GitHub CLI's default issue-list behavior returns the most recent open items.
When the repository has >1000 open issues, an old unprocessed review claim can
therefore be outside the fetched window forever. Sorting after truncation cannot
recover an item that was never enumerated.

No network, credentials, wallets, or production mutations are used.
"""

TOTAL_OPEN = 1311
FETCH_LIMIT = 1000

# Model 1,311 open issues numbered oldest -> newest. The oldest issue is a
# review claim that the backfill exists to rescue. All others are unrelated.
issues = [
    {
        "number": n,
        "title": "[Bounty Claim] PR Review - old stranded claim" if n == 1 else f"ordinary open issue {n}",
        "labels": [],
    }
    for n in range(1, TOTAL_OPEN + 1)
]


def is_review_claim(title):
    return "pr review" in title.lower()


# `gh issue list --limit 1000` defaults to the most recent open items.
returned = list(reversed(issues))[:FETCH_LIMIT]

# Current backfill classification + its later oldest-first sorting.
never = []
for issue in returned:
    if is_review_claim(issue["title"]):
        never.append(issue["number"])
never = sorted(never)

omitted = {i["number"] for i in issues} - {i["number"] for i in returned}

print("total_open         =", TOTAL_OPEN)
print("fetch_limit        =", FETCH_LIMIT)
print("returned_count     =", len(returned))
print("omitted_count      =", len(omitted))
print("oldest_returned    =", min(i["number"] for i in returned))
print("claim_1_enumerated =", 1 not in omitted)
print("backfill_never     =", never)

assert len(returned) == 1000
assert len(omitted) == 311
assert 1 in omitted
assert never == []

print("REPRODUCED: oldest unprocessed review claim is invisible before oldest-first sorting")
