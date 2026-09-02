#!/usr/bin/env python3
"""Remove non-opportunity/claim artifacts from the generated RTC queue.

This is deliberately conservative. It only removes issues whose titles are
strongly indicative of a claimant's submission, payout request, transfer
request, adjudication request, or historical PR-review batch rather than a
maintainer-authored opportunity. It never changes RTC accounting stages.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

JSON_PATH = Path("artifacts/rtc-candidate-queue.json")
MD_PATH = Path("artifacts/rtc-candidate-queue.md")

NON_OPPORTUNITY = re.compile(
    r"^(?:\s*\[(?:claim|bounty claim|wallet|payout|submission|delivery)\b|"
    r"\s*(?:claim\s*:|claim\b|bounty claim\b|rtc bounty claim\b|"
    r"wallet transfer request\b|wallet transfer\b|rtc payout\b|payout request\b|"
    r"delivery review request\b|agent economy delivery review request\b|"
    r"pr review\s*[-:]|pr reviews\s*[-:]|submission\s*[-:]))",
    re.I,
)

CLAIM_BODY = re.compile(
    r"\b(?:claimant|request(?:ed)? payout|payout target|wallet transfer request|"
    r"this is my submission|submission for|ready for review)\b",
    re.I,
)

# Titles that can contain the word "claim" while still defining a bounty.
BOUNTY_DEFINITION = re.compile(
    r"\[(?:bounty|tool|docs?|grant|task|content|research|sdk|integration|fix|bugfix)\b|"
    r"\b(?:bounty|reward|payout)\s*[:=-]?\s*(?:up to\s*)?\d+(?:\.\d+)?\s*rtc\b",
    re.I,
)


def is_non_opportunity(candidate: dict) -> bool:
    title = str(candidate.get("title") or "").strip()
    if BOUNTY_DEFINITION.search(title):
        return False
    if NON_OPPORTUNITY.search(title):
        return True
    # Generated candidates do not necessarily carry the issue body. If future
    # versions add it, use it only as a secondary signal.
    body = str(candidate.get("body") or "")
    if body and CLAIM_BODY.search(body) and not BOUNTY_DEFINITION.search(title):
        return True
    return False


def render_markdown(data: dict) -> str:
    rows = data.get("candidates") or []
    lines = [
        "# RTC Candidate Queue",
        "",
        "Triage only. No item below is earned RTC. Every FINAL_VERIFY item still requires authoritative issue-level verification before work begins.",
        "",
        f"Generated: {data.get('generated_at', 'unknown')}",
        f"Candidates after claim-artifact sanitation: {len(rows)}",
        f"FINAL_VERIFY: {sum(1 for row in rows if row.get('decision') == 'FINAL_VERIFY')}",
        "",
        "| Decision | Repo | Issue | RTC | EV index | Route | Title |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for row in rows[:250]:
        title = str(row.get("title") or "").replace("|", "\\|")
        lines.append(
            f"| {row.get('decision','')} | {row.get('repository','')} | "
            f"#{row.get('number','')} | {row.get('reward_rtc',0)} | "
            f"{row.get('ev_index',0)} | {row.get('route','')} | {title} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    data = json.loads(JSON_PATH.read_text())
    before = list(data.get("candidates") or [])
    kept = [row for row in before if not is_non_opportunity(row)]
    removed = len(before) - len(kept)
    data["candidates"] = kept
    data["candidate_count"] = len(kept)
    data["final_verify_count"] = sum(1 for row in kept if row.get("decision") == "FINAL_VERIFY")
    data["sanitizer"] = {
        "removed_non_opportunity_claim_artifacts": removed,
        "policy": "conservative-title-filter-v1",
    }
    JSON_PATH.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n")
    MD_PATH.write_text(render_markdown(data))
    print(f"sanitized RTC queue: kept={len(kept)} removed={removed} final_verify={data['final_verify_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
