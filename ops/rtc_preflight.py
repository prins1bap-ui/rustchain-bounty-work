#!/usr/bin/env python3
"""Build a high-EV RustChain bounty queue from authoritative GitHub state.

Triage only. This script NEVER promotes accounting stages or treats advertised
RTC as earned. It exists to fail closed on unsafe, duplicate, saturated,
unsubmittable, or eligibility-gated work before implementation time is spent.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

OWNER = "Scottcjn"
REPO = "rustchain-bounties"
API = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN", "")
UA = "prins1bap-ui-rtc-preflight"

OWN_WORK = {
    29, 100, 254, 293, 315, 398, 402, 520, 685, 747, 1102, 13226,
    13954, 14014, 1524, 1618, 2143, 2784, 12442, 12443, 12444, 16601,
}

CLAIM_SIGNAL = re.compile(
    r"\b(claim(?:ing|ed)?|implemented|completed|submitted|ready for review|"
    r"pull request|\bpr\s*#|merged|delivered)\b",
    re.I,
)
OFFENSIVE_TITLE = re.compile(
    r"\b(red[- ]?team|break\b|attacks?\b|exploit|vulnerab(?:ility)?\s+hunt|"
    r"bug bounty|security season|adversarial|double[- ]?spend|csrf|xss|rce|"
    r"auth bypass|privilege escalation|replay\s*&?\s*relay)\b",
    re.I,
)
DEFENSIVE_TITLE = re.compile(
    r"\b(harden|hardening|remediation|secure coding|validation|anti[- ]?spoof|"
    r"regression test|defensive|sanitize|least privilege)\b",
    re.I,
)
FUND_TITLE = re.compile(
    r"\b(liquidity|tips?|donat|swap|bridge|escrow|staking?|x402|payment|"
    r"wallet linking|transaction test|send rtc|transfer rtc)\b",
    re.I,
)
EXTERNAL_TITLE = re.compile(
    r"\b(youtube|videos?|article|blog|social media|reddit|twitter|mastodon|"
    r"dev\.to|medium|hashnode|publication|ambassador|referral|hacker news|"
    r"review of|auto[- ]?post|backlinks?|engagement challenge|directories|registries)\b",
    re.I,
)
HARDWARE_TITLE = re.compile(
    r"\b(playtest|hardware report|test the miner|run the miner|run a full node|"
    r"real hardware|powerpc|sparc|risc[- ]?v|mips|s390x|mac os 9|amiga|"
    r"dreamcast|raspberry pi|vintage hardware|dos miner|port .* miner)\b",
    re.I,
)
ELIGIBILITY_TITLE = re.compile(
    r"\b(maintainer[- ]nominated|nomination|invite[- ]only|invitation only|"
    r"selected contributors?|first[- ]right[- ]of[- ]claim|priority claim|"
    r"pre[- ]approved|approved applicants?)\b",
    re.I,
)

PR_ROUTE = re.compile(
    r"\b(PRs? go to|PRs? against|open a PR|submit a PR|PR to `?Scottcjn/|"
    r"pull request to `?Scottcjn/|deliverable:\s*a PR)\b",
    re.I,
)
STANDALONE_ROUTE = re.compile(
    r"\b(standalone repo|standalone repository|open source on GitHub|"
    r"submit as standalone)\b",
    re.I,
)
EMAIL_ROUTE = re.compile(
    r"\b(email|sophia\.eagent@gmail\.com|submit:\s*\[[^\]]*email)\b",
    re.I,
)

REWARD_TITLE = [
    re.compile(r"\b(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*RTC\b", re.I),
    re.compile(r"\bup to\s+(\d+(?:\.\d+)?)\s*RTC\b", re.I),
    re.compile(r"\b(\d+(?:\.\d+)?)\s*RTC\b", re.I),
]


def api(path: str, params: dict | None = None):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": UA}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def reward_from_title(title: str) -> float:
    for index, pattern in enumerate(REWARD_TITLE):
        match = pattern.search(title or "")
        if match:
            return float(match.group(2) if index == 0 else match.group(1))
    return 0.0


def reward_from_body(body: str) -> float:
    patterns = [
        re.compile(r"\breward(?:_rtc)?\s*[:=]\s*\*{0,2}(\d+(?:\.\d+)?)", re.I),
        re.compile(r"\bpayout\s*[:=]\s*\*{0,2}(\d+(?:\.\d+)?)\s*RTC", re.I),
    ]
    values: list[float] = []
    for pattern in patterns:
        values.extend(float(value) for value in pattern.findall(body or "") if float(value) <= 1000)
    return max(values, default=0.0)


@dataclass
class Candidate:
    number: int
    title: str
    url: str
    reward_rtc: float
    comments: int
    claim_signals: int
    route: str
    flags: list[str]
    score: float
    decision: str


def classify(number: int, title: str, body: str) -> tuple[str, list[str]]:
    text = f"{title}\n{body}"
    title_text = title or ""
    lower = (body or "").lower()
    flags: list[str] = []

    if number in OWN_WORK:
        flags.append("existing-user-work")
    if ELIGIBILITY_TITLE.search(title_text) or any(
        marker in lower for marker in (
            "must be nominated", "maintainer nomination", "requires nomination",
            "priority claimant", "first right of claim", "first-right-of-claim",
        )
    ):
        flags.append("eligibility-gated")

    offensive = bool(OFFENSIVE_TITLE.search(title_text))
    defensive = bool(DEFENSIVE_TITLE.search(title_text))
    if offensive and not defensive:
        flags.append("offensive-security")
    elif defensive:
        flags.append("defensive-security")

    fund_body_markers = (
        "must use real rtc", "provide liquidity", "transaction hash", "funded wallet",
        "wallet to post jobs", "real rtc on mainnet", "link a wallet via the api",
        "send a tip", "tip the", "make a payment", "escrow release",
    )
    if FUND_TITLE.search(title_text) or any(marker in lower for marker in fund_body_markers):
        flags.append("fund-movement")

    external_body_markers = (
        "must be on youtube", "publish on dev.to", "publish on medium", "publish on hashnode",
        "post on social media", "share on social", "real audience", "public youtube video",
        "discord server", "subscriber", "posted to reddit", "publish to moltbook",
        "post to moltbook", "post to discord", "post to twitter", "upload to bottube",
        "publish on bottube", "crates.io", "npm publish", "submit to directories",
    )
    if EXTERNAL_TITLE.search(title_text) or any(marker in lower for marker in external_body_markers):
        flags.append("external-publication/account")

    hardware_body_markers = (
        "must run on real hardware", "screenshot/video of miner running", "your hardware/os",
        "average fps", "run the miner for 24 hours", "real machine", "physical hardware",
    )
    if HARDWARE_TITLE.search(title_text) or any(marker in lower for marker in hardware_body_markers):
        flags.append("hardware/user-presence")

    if PR_ROUTE.search(text):
        route = "pr-only"
    elif STANDALONE_ROUTE.search(text):
        route = "standalone"
    elif EMAIL_ROUTE.search(text):
        route = "email-fallback"
    else:
        route = "email-fallback"

    return route, flags


def claim_signal_count(number: int) -> int:
    try:
        comments = api(f"/repos/{OWNER}/{REPO}/issues/{number}/comments", {"per_page": 100})
    except Exception:
        return -1
    return sum(1 for comment in comments if CLAIM_SIGNAL.search(comment.get("body") or ""))


def main() -> int:
    issues: list[dict] = []
    for page in range(1, 16):
        batch = api(
            f"/repos/{OWNER}/{REPO}/issues",
            {"state": "open", "labels": "bounty", "per_page": 100, "page": page},
        )
        if not batch:
            break
        issues.extend(item for item in batch if "pull_request" not in item)
        if len(batch) < 100:
            break

    raw: list[tuple] = []
    for issue in issues:
        title = issue.get("title", "")
        body = issue.get("body") or ""
        reward = reward_from_title(title) or reward_from_body(body)
        if reward <= 0:
            continue
        route, flags = classify(issue["number"], title, body)
        raw.append((reward, issue, route, flags))
    raw.sort(key=lambda row: row[0], reverse=True)

    candidates: list[Candidate] = []
    for index, (reward, issue, route, flags) in enumerate(raw):
        claims = claim_signal_count(issue["number"]) if reward >= 20 and index < 120 else -1
        comments = int(issue.get("comments") or 0)
        flagset = set(flags)

        penalty = 0.0
        if "existing-user-work" in flagset:
            penalty += 1000
        if "offensive-security" in flagset:
            penalty += 1000
        if "fund-movement" in flagset:
            penalty += 1000
        if "external-publication/account" in flagset:
            penalty += 250
        if "hardware/user-presence" in flagset:
            penalty += 250
        if "eligibility-gated" in flagset:
            penalty += 250
        if "defensive-security" in flagset:
            penalty += 20
        if route == "pr-only":
            penalty += 100
        if claims == -1 and reward >= 20:
            penalty += 30
        elif claims > 0:
            penalty += min(150, claims * 12)
        if comments > 25:
            penalty += min(50, comments / 3)

        score = round(reward - penalty, 2)

        if "existing-user-work" in flagset:
            decision = "OWN_WORK_RECHECK"
        elif {"offensive-security", "fund-movement"} & flagset:
            decision = "EXCLUDE"
        elif "eligibility-gated" in flagset:
            decision = "BLOCKED_ELIGIBILITY"
        elif {"external-publication/account", "hardware/user-presence"} & flagset:
            decision = "BLOCKED_USER_OR_EXTERNAL"
        elif claims == -1 and reward >= 20:
            decision = "VERIFY"
        elif claims >= 5:
            decision = "SATURATION_RECHECK"
        elif route == "pr-only":
            decision = "DEFER_ROUTE"
        elif "defensive-security" in flagset:
            decision = "VERIFY"
        elif score >= 40:
            decision = "EXECUTE"
        elif score >= 15:
            decision = "VERIFY"
        else:
            decision = "DEFER"

        candidates.append(Candidate(
            issue["number"], issue.get("title", ""), issue["html_url"], reward,
            comments, claims, route, flags, score, decision,
        ))
        time.sleep(0.015)

    priority = {
        "EXECUTE": 8,
        "VERIFY": 7,
        "SATURATION_RECHECK": 6,
        "DEFER_ROUTE": 5,
        "DEFER": 4,
        "OWN_WORK_RECHECK": 3,
        "BLOCKED_ELIGIBILITY": 2,
        "BLOCKED_USER_OR_EXTERNAL": 1,
        "EXCLUDE": 0,
    }
    candidates.sort(key=lambda item: (priority[item.decision], item.score, item.reward_rtc), reverse=True)

    Path("artifacts").mkdir(exist_ok=True)
    payload = {
        "source": f"https://github.com/{OWNER}/{REPO}/issues",
        "accounting_note": "Triage only. No item here is earned RTC.",
        "candidate_count": len(candidates),
        "candidates": [asdict(candidate) for candidate in candidates],
    }
    Path("artifacts/rtc-candidate-queue.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# RTC Candidate Queue", "", "Triage only. Nothing here is earned RTC.", "",
        "| Decision | RTC | # | Route | Claim signals | Score | Title |",
        "|---|---:|---:|---|---:|---:|---|",
    ]
    for candidate in candidates[:150]:
        safe_title = candidate.title.replace("|", "/")
        lines.append(
            f"| {candidate.decision} | {candidate.reward_rtc:g} | [{candidate.number}]({candidate.url}) | "
            f"{candidate.route} | {candidate.claim_signals} | {candidate.score:g} | {safe_title} |"
        )
    Path("artifacts/rtc-candidate-queue.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"ranked {len(candidates)} bounties")
    for candidate in [item for item in candidates if item.decision == "EXECUTE"][:15]:
        print(f"EXECUTE #{candidate.number}: {candidate.reward_rtc:g} RTC score={candidate.score:g} route={candidate.route} {candidate.title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
