#!/usr/bin/env python3
"""Model bounty_payout.py candidate construction for comment-only eligibility."""

# An old claim is intentionally eligible only through a trusted
# `Verified eligible` comment, not the bounty-eligible label.
manual_verified_issue = 1
label_eligible = set()

# Current code's fallback candidate sweep only includes 400 recent open issues.
recent_open = set(range(2, 402))

candidates = label_eligible | recent_open

print({
    "manual_verified_issue": manual_verified_issue,
    "in_label_pass": manual_verified_issue in label_eligible,
    "in_recent_400": manual_verified_issue in recent_open,
    "ever_reaches_comment_eligibility_check": manual_verified_issue in candidates,
})

assert manual_verified_issue not in candidates
