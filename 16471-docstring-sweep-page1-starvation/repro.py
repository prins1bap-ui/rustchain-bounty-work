#!/usr/bin/env python3
"""Deterministic model of docstring-gate.yml's scheduled discovery cap."""

PER_PAGE = 60

# 61 open claims are all still labelled awaiting-merge.
awaiting_merge = list(range(1, 62))


def github_search_page_1():
    # Current workflow requests per_page=60 and never requests page=2.
    return awaiting_merge[:PER_PAGE]


seen = set()
for sweep in range(1, 6):
    discovered = github_search_page_1()
    seen.update(discovered)
    print(f"sweep={sweep} discovered={len(discovered)} contains_61={61 in discovered}")

print(f"ever_seen_61={61 in seen}")
assert 61 not in seen
