#!/usr/bin/env python3
"""Rank RTC candidates by expected collected value per hour.

Input: ops/candidate_queue.json
Each candidate may contain:
  id, reward_rtc, acceptance_probability,
  payout_probability_given_acceptance, estimated_hours,
  recent_settlement_evidence, competition_count

The script never treats a missing probability as certain. Missing required
numeric fields make a candidate unscored rather than optimistically ranked.
"""

from __future__ import annotations

import json
from pathlib import Path

QUEUE = Path(__file__).with_name("candidate_queue.json")


def score(candidate: dict) -> float | None:
    required = (
        "reward_rtc",
        "acceptance_probability",
        "payout_probability_given_acceptance",
        "estimated_hours",
    )
    if any(candidate.get(k) is None for k in required):
        return None

    reward = float(candidate["reward_rtc"])
    p_accept = float(candidate["acceptance_probability"])
    p_payout = float(candidate["payout_probability_given_acceptance"])
    hours = float(candidate["estimated_hours"])
    if reward < 0 or hours <= 0:
        return None
    if not (0 <= p_accept <= 1 and 0 <= p_payout <= 1):
        return None

    base = reward * p_accept * p_payout / hours

    # Settlement evidence is a modest multiplier, never a substitute for the
    # base economics. Competition is a modest penalty.
    settlement = float(candidate.get("recent_settlement_evidence", 0.5))
    settlement = min(1.0, max(0.0, settlement))
    competition = max(0, int(candidate.get("competition_count", 0)))

    settlement_multiplier = 0.75 + 0.5 * settlement
    competition_multiplier = 1.0 / (1.0 + 0.35 * competition)
    return base * settlement_multiplier * competition_multiplier


def main() -> None:
    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    ranked = []
    unscored = []

    for candidate in data.get("candidates", []):
        value = score(candidate)
        if value is None:
            unscored.append(candidate)
        else:
            ranked.append((value, candidate))

    ranked.sort(key=lambda item: item[0], reverse=True)

    print("RTC candidate ranking")
    print("=====================")
    for index, (value, candidate) in enumerate(ranked, 1):
        print(
            f"{index:>2}. {candidate.get('id', '<unnamed>')}: "
            f"{value:.3f} adjusted expected RTC/hour"
        )

    if unscored:
        print("\nUNSCORED — missing or invalid required economics")
        for candidate in unscored:
            print(f"- {candidate.get('id', '<unnamed>')}")


if __name__ == "__main__":
    main()
