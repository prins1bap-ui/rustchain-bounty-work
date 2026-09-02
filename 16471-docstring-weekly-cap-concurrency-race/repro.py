#!/usr/bin/env python3
"""Deterministic model of two concurrent docstring-gate decisions."""

MAX_RTC_PER_WEEK = 40.0
already = 30.0
claim_a = 10.0
claim_b = 10.0

# Both independent workflow runs read the same committed pre-approval state.
a_reads = already
b_reads = already

a_approves = a_reads + claim_a <= MAX_RTC_PER_WEEK
b_approves = b_reads + claim_b <= MAX_RTC_PER_WEEK

final_verified = already
if a_approves:
    final_verified += claim_a
if b_approves:
    final_verified += claim_b

print({
    "a_reads": a_reads,
    "b_reads": b_reads,
    "a_approves": a_approves,
    "b_approves": b_approves,
    "final_verified": final_verified,
    "weekly_cap": MAX_RTC_PER_WEEK,
})

assert a_approves and b_approves
assert final_verified == 50.0
assert final_verified > MAX_RTC_PER_WEEK
