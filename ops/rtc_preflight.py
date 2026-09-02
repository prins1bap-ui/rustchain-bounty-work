#!/usr/bin/env python3
"""Build a high-EV RustChain bounty queue from authoritative GitHub issue state.

Triage accelerator only. It never marks RTC earned. The queue exists to spend
seconds, not tens of minutes, eliminating saturated, unsafe, or route-blocked
work before implementation begins.
"""
from __future__ import annotations
import json, os, re, time, urllib.parse, urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path

OWNER = "Scottcjn"
REPO = "rustchain-bounties"
API = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN", "")
UA = "prins1bap-ui-rtc-preflight"

CLAIM = re.compile(r"\b(claim(?:ing)?|implemented|complete(?:d)?|submitted|pull request|pr\s*#|ready for review)\b", re.I)
EMAIL = re.compile(r"\b(email|sophia\.eagent@gmail\.com|submit:\s*\[[^\]]*email)\b", re.I)
STANDALONE = re.compile(r"\b(standalone repo|standalone repository|open source on github)\b", re.I)
PR_ONLY = re.compile(r"\b(prs? (?:go|against|to)|open a pr|submit a pr|pull request)\b", re.I)

OFFENSIVE_TITLE = re.compile(r"\b(red[- ]?team|break\b|exploit|attack|vulnerability hunt|bug bounty|adversarial)\b", re.I)
DEFENSIVE_TITLE = re.compile(r"\b(harden|hardening|remediation|fix|validation|anti-spoof|regression test|secure coding)\b", re.I)
FUND_TITLE = re.compile(r"\b(liquidity|swap|bridge|escrow|transaction test|staking|wallet linking|payment integration)\b", re.I)
EXTERNAL_TITLE = re.compile(r"\b(youtube|video|article|blog|social|review|reddit|twitter|mastodon|dev\.to|medium|hashnode|publication)\b", re.I)
HARDWARE_TITLE = re.compile(r"\b(playtest|hardware report|test the miner|real hardware|powerpc|sparc|risc-v|mac os 9|raspberry pi|vintage hardware)\b", re.I)

REWARD_TITLE = [
    re.compile(r"\b(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*RTC\b", re.I),
    re.compile(r"\bup to\s+(\d+(?:\.\d+)?)\s*RTC\b", re.I),
    re.compile(r"\b(\d+(?:\.\d+)?)\s*RTC\b", re.I),
]

def api(path, params=None):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": UA}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read())

def reward_from_title(title):
    for i, pattern in enumerate(REWARD_TITLE):
        match = pattern.search(title or "")
        if not match:
            continue
        return float(match.group(2) if i == 0 else match.group(1))
    return 0.0

def reward_from_body(body):
    patterns = [
        re.compile(r"\breward(?:_rtc)?\s*[:=]\s*\*{0,2}(\d+(?:\.\d+)?)\b", re.I),
        re.compile(r"\bpayout\s*[:=]\s*\*{0,2}(\d+(?:\.\d+)?)\s*RTC\b", re.I),
        re.compile(r"\b(\d+(?:\.\d+)?)\s*RTC\b", re.I),
    ]
    values = []
    for pattern in patterns:
        values.extend(float(x) for x in pattern.findall(body or "") if float(x) <= 1000)
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

def classify(body, title):
    text = f"{title}\n{body}"
    body_l = (body or "").lower()
    flags = []

    offensive = bool(OFFENSIVE_TITLE.search(title or ""))
    defensive = bool(DEFENSIVE_TITLE.search(title or ""))
    if offensive and not defensive:
        flags.append("offensive-security")
    elif defensive and re.search(r"\b(security|spoof|auth|validation|vulnerab|attack)\b", text, re.I):
        flags.append("defensive-security")

    if FUND_TITLE.search(title or "") or any(p in body_l for p in (
        "must use real rtc", "provide liquidity", "transaction hash required",
        "link a wallet via the api", "funded wallet to post jobs"
    )):
        flags.append("fund-movement")

    if EXTERNAL_TITLE.search(title or "") or any(p in body_l for p in (
        "must be on youtube", "publish on dev.to", "publish on medium",
        "post on social media", "share on social", "real audience"
    )):
        flags.append("external-publication/account")

    if HARDWARE_TITLE.search(title or "") or any(p in body_l for p in (
        "must run on real hardware", "screenshot/video of miner running",
        "your hardware/os and average fps", "run the miner for 24 hours"
    )):
        flags.append("hardware/user-presence")

    if EMAIL.search(text):
        route = "email-fallback"
    elif STANDALONE.search(text):
        route = "standalone"
    elif PR_ONLY.search(text):
        route = "pr-only"
    else:
        route = "comment-or-unspecified"
    return route, flags

def claim_signal_count(number):
    try:
        comments = api(f"/repos/{OWNER}/{REPO}/issues/{number}/comments", {"per_page":100})
    except Exception:
        return -1
    return sum(1 for comment in comments if CLAIM.search(comment.get("body") or ""))

def main():
    issues = []
    for page in range(1, 16):
        batch = api(f"/repos/{OWNER}/{REPO}/issues", {
            "state":"open", "labels":"bounty", "per_page":100, "page":page
        })
        if not batch:
            break
        issues.extend(item for item in batch if "pull_request" not in item)
        if len(batch) < 100:
            break

    raw = []
    for issue in issues:
        title = issue.get("title", "")
        body = issue.get("body") or ""
        reward = reward_from_title(title) or reward_from_body(body)
        if reward <= 0:
            continue
        route, flags = classify(body, title)
        raw.append((reward, issue, route, flags))
    raw.sort(key=lambda row: row[0], reverse=True)

    candidates = []
    for index, (reward, issue, route, flags) in enumerate(raw):
        title = issue.get("title", "")
        claims = claim_signal_count(issue["number"]) if reward >= 20 and index < 120 else -1
        comments = int(issue.get("comments") or 0)

        penalty = 0.0
        if "offensive-security" in flags: penalty += 500
        if "fund-movement" in flags: penalty += 500
        if "external-publication/account" in flags: penalty += 140
        if "hardware/user-presence" in flags: penalty += 140
        if "defensive-security" in flags: penalty += 15
        if route == "pr-only": penalty += 35
        if claims > 0: penalty += min(100, claims * 10)
        if comments > 25: penalty += min(35, comments / 4)

        score = round(reward - penalty, 2)
        flagset = set(flags)
        hard = {"offensive-security", "fund-movement"} & flagset
        user_dep = {"external-publication/account", "hardware/user-presence"} & flagset

        if hard:
            decision = "EXCLUDE"
        elif user_dep:
            decision = "BLOCKED_USER_OR_EXTERNAL"
        elif claims >= 5:
            decision = "SATURATION_RECHECK"
        elif route == "pr-only" and reward < 50:
            decision = "DEFER_ROUTE"
        elif score >= 40:
            decision = "EXECUTE"
        elif score >= 15:
            decision = "VERIFY"
        else:
            decision = "DEFER"

        candidates.append(Candidate(
            issue["number"], title, issue["html_url"], reward, comments, claims,
            route, flags, score, decision
        ))
        time.sleep(0.02)

    rank_order = {
        "EXECUTE": 6, "VERIFY": 5, "SATURATION_RECHECK": 4, "DEFER_ROUTE": 3,
        "DEFER": 2, "BLOCKED_USER_OR_EXTERNAL": 1, "EXCLUDE": 0
    }
    candidates.sort(key=lambda c: (rank_order[c.decision], c.score, c.reward_rtc), reverse=True)

    output = {
        "source": f"https://github.com/{OWNER}/{REPO}/issues",
        "accounting_note": "Triage only. No item here is earned RTC.",
        "candidate_count": len(candidates),
        "candidates": [asdict(c) for c in candidates],
    }
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/rtc-candidate-queue.json").write_text(json.dumps(output, indent=2), encoding="utf-8")

    rows = [
        "# RTC Candidate Queue", "",
        "Triage only. Nothing here is earned RTC.", "",
        "| Decision | RTC | # | Route | Claim signals | Score | Title |",
        "|---|---:|---:|---|---:|---:|---|"
    ]
    for candidate in candidates[:120]:
        safe_title = candidate.title.replace("|", "/")
        rows.append(
            f"| {candidate.decision} | {candidate.reward_rtc:g} | "
            f"[{candidate.number}]({candidate.url}) | {candidate.route} | "
            f"{candidate.claim_signals} | {candidate.score:g} | {safe_title} |"
        )
    Path("artifacts/rtc-candidate-queue.md").write_text("\n".join(rows) + "\n", encoding="utf-8")

    print(f"ranked {len(candidates)} bounties")
    for candidate in [x for x in candidates if x.decision == "EXECUTE"][:15]:
        print(f"EXECUTE #{candidate.number}: {candidate.reward_rtc:g} RTC score={candidate.score:g} route={candidate.route} {candidate.title}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
