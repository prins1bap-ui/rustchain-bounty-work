#!/usr/bin/env python3
"""Normalize RTC opportunity queue after discovery.

Policy:
- Never changes accounting stages.
- Removes obvious claim/payment/tracking records.
- Treats an explicit RTC value in the authoritative issue title as the
  controlling advertised reward for triage. Body values remain informational
  because they frequently contain pools, old amounts, or examples.
- Recomputes the execution decision conservatively from existing route,
  competition, and safety flags.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

JSON_PATH = Path("artifacts/rtc-candidate-queue.json")
MD_PATH = Path("artifacts/rtc-candidate-queue.md")

NON_OPPORTUNITY = re.compile(
    r"^(?:\s*\[(?:claim|bounty claim|wallet|payout|submission|delivery|tracking)\b|"
    r"\s*(?:claim\s*:|claim\b|bounty claim\b|rtc bounty claim\b|"
    r"wallet transfer request\b|wallet transfer\b|rtc payout\b|payout request\b|"
    r"delivery review request\b|agent economy delivery review request\b|"
    r"pr review\s*[-:]|pr reviews\s*[-:]|submission\s*[-:]))",
    re.I,
)

OFFENSIVE_TITLE = re.compile(
    r"\b(red[- ]?team|exploit|vulnerability hunt|bug bounty|double[- ]?spend|"
    r"auth bypass|privilege escalation|csrf|xss|rce|replay attack)\b",
    re.I,
)

EXTERNAL_TITLE = re.compile(
    r"\b(upload .*videos?|youtube|reddit|twitter|mastodon|medium|dev\.to|hashnode|"
    r"social media|ambassador|referral|discord|moltbook|publish(?:ing)? to)\b",
    re.I,
)


def is_non_opportunity(row: dict) -> bool:
    return bool(NON_OPPORTUNITY.search(str(row.get("title") or "").strip()))


def decide(row: dict) -> str:
    title = str(row.get("title") or "")
    flags = set(row.get("flags") or [])
    if OFFENSIVE_TITLE.search(title):
        return "EXCLUDE"
    if "existing-user-work" in flags:
        return "OWN_WORK_RECHECK"
    if {"offensive-security", "fund-movement"} & flags:
        return "EXCLUDE"
    if EXTERNAL_TITLE.search(title):
        return "BLOCKED_USER_OR_EXTERNAL"
    if {"eligibility-gated", "external-publication/account", "hardware/user-presence"} & flags:
        return "BLOCKED_USER_OR_EXTERNAL"
    comp_status = row.get("competition_status")
    awards = int(row.get("maintainer_awards") or 0)
    completed = int(row.get("competitor_completed") or 0)
    route = str(row.get("route") or "unknown")
    if comp_status != "ok":
        return "VERIFY_COMPETITION"
    if awards or completed >= 2:
        return "DEFER_SATURATED"
    if route in {"merge-gated", "pr-only"}:
        return "DEFER_ROUTE"
    if route == "unknown":
        return "VERIFY_ROUTE"
    if "defensive-security" in flags:
        return "VERIFY_SAFETY"
    if completed == 1:
        return "VERIFY_COMPETITION"
    if "pool-or-program-reward" in flags:
        return "VERIFY_REWARD"
    return "FINAL_VERIFY"


def normalize_row(row: dict) -> dict:
    title_reward = float(row.get("reward_title_rtc") or 0)
    body_reward = float(row.get("reward_body_rtc") or 0)
    controlling = title_reward if title_reward > 0 else body_reward
    row["reward_rtc"] = controlling
    row["reward_policy"] = "authoritative-title-first" if title_reward > 0 else "body-fallback"
    row["reward_conflict"] = bool(title_reward > 0 and body_reward > 0 and abs(title_reward - body_reward) > 0.01)
    row["decision"] = decide(row)

    # Preserve relative EV logic while removing body/pool inflation. The exact
    # index is triage-only, so scale the old score by the reward correction.
    old_reward = max(title_reward, body_reward, 0.000001)
    old_ev = float(row.get("ev_index") or 0)
    row["ev_index"] = round(old_ev * (controlling / old_reward), 3) if controlling > 0 else 0.0
    return row


def render_markdown(data: dict) -> str:
    rows = data.get("candidates") or []
    priority = {
        "FINAL_VERIFY": 10, "VERIFY_ROUTE": 9, "VERIFY_COMPETITION": 8,
        "VERIFY_SAFETY": 7, "VERIFY_REWARD": 6, "DEFER_ROUTE": 5,
        "DEFER_SATURATED": 4, "OWN_WORK_RECHECK": 3,
        "BLOCKED_USER_OR_EXTERNAL": 2, "EXCLUDE": 0,
    }
    rows.sort(key=lambda r: (priority.get(r.get("decision"), 1), float(r.get("ev_index") or 0), float(r.get("reward_rtc") or 0)), reverse=True)
    lines = [
        "# RTC Candidate Queue",
        "",
        "Triage only. No item below is earned RTC. FINAL_VERIFY still requires live issue-level verification before work begins.",
        "",
        f"Generated: {data.get('generated_at', 'unknown')}",
        f"Candidates: {len(rows)}",
        f"FINAL_VERIFY: {sum(1 for r in rows if r.get('decision') == 'FINAL_VERIFY')}",
        "",
        "| Decision | Repo/# | RTC | EV index | Route | Competition I/C/A | Reward policy | Title |",
        "|---|---|---:|---:|---|---:|---|---|",
    ]
    for row in rows[:250]:
        title = str(row.get("title") or "").replace("|", "/")
        lines.append(
            f"| {row.get('decision','')} | {row.get('repository','')}#{row.get('number','')} | "
            f"{row.get('reward_rtc',0)} | {row.get('ev_index',0)} | {row.get('route','')} | "
            f"{row.get('competitor_intent',0)}/{row.get('competitor_completed',0)}/{row.get('maintainer_awards',0)} | "
            f"{row.get('reward_policy','')} | {title} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    data = json.loads(JSON_PATH.read_text())
    before = list(data.get("candidates") or [])
    kept = [normalize_row(dict(row)) for row in before if not is_non_opportunity(row)]
    removed = len(before) - len(kept)

    priority = {
        "FINAL_VERIFY": 10, "VERIFY_ROUTE": 9, "VERIFY_COMPETITION": 8,
        "VERIFY_SAFETY": 7, "VERIFY_REWARD": 6, "DEFER_ROUTE": 5,
        "DEFER_SATURATED": 4, "OWN_WORK_RECHECK": 3,
        "BLOCKED_USER_OR_EXTERNAL": 2, "EXCLUDE": 0,
    }
    kept.sort(key=lambda r: (priority.get(r.get("decision"), 1), float(r.get("ev_index") or 0), float(r.get("reward_rtc") or 0)), reverse=True)

    data["candidates"] = kept
    data["candidate_count"] = len(kept)
    data["final_verify_count"] = sum(1 for row in kept if row.get("decision") == "FINAL_VERIFY")
    data["sanitizer"] = {
        "removed_non_opportunity_records": removed,
        "reward_policy": "authoritative-title-first; body-fallback only when title has no RTC value",
        "policy_version": 2,
    }
    JSON_PATH.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n")
    MD_PATH.write_text(render_markdown(data))
    print(f"normalized RTC queue: kept={len(kept)} removed={removed} final_verify={data['final_verify_count']}")
    for row in [r for r in kept if r.get("decision") == "FINAL_VERIFY"][:20]:
        print(f"FINAL_VERIFY {row.get('repository')}#{row.get('number')}: {row.get('reward_rtc')} RTC ev={row.get('ev_index')} {row.get('title')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
