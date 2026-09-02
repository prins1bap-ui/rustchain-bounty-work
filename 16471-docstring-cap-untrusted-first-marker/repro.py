#!/usr/bin/env python3
"""Model current docstring_rtc_this_week() marker selection."""
import re

comments = [
    {"author": "claimant", "body": "pre-seeded <!-- rtc-payout-amount: 0 -->"},
    {"author": "github-actions", "body": "verified <!-- rtc-payout-amount: 25 -->"},
]

total = 0.0
selected = None
for c in comments:
    m = re.search(r'<!--\s*rtc-payout-amount:\s*([\d.]+)\s*-->', c["body"])
    if m:
        selected = float(m.group(1))
        total += selected
        break

print({"selected_marker": selected, "true_gate_amount": 25.0, "weekly_cap_counted": total})
assert selected == 0.0
