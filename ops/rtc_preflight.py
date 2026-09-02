#!/usr/bin/env python3
"""Build a high-EV RustChain bounty queue from authoritative GitHub issue state.

This is a triage accelerator, not an accounting source. It never marks RTC earned.
It ranks candidates and records why apparently large bounties should be rejected
before implementation time is spent.
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

SECURITY = re.compile(r"\b(red[- ]?team|vulnerab|exploit|attack|bypass|spoof|double[- ]?spend|rce|csrf|xss|break the|adversarial)\b", re.I)
FUND = re.compile(r"\b(liquidity|transfer|swap|bridge|escrow|stake|staking|funded wallet|transaction test|move funds|send rtc)\b", re.I)
EXTERNAL = re.compile(r"\b(youtube|dev\.to|medium|hashnode|reddit|twitter|mastodon|discord|social media|real audience|subscriber|publish(?:ed)?|video upload)\b", re.I)
HARDWARE = re.compile(r"\b(real hardware|your machine|hardware report|screenshot|24[- ]?hour|powerpc|sparc|risc-v|mac os 9|vintage hardware|playtest)\b", re.I)
CLAIM = re.compile(r"\b(claim(?:ing)?|implemented|complete(?:d)?|submitted|pull request|pr\s*#|ready for review)\b", re.I)
EMAIL = re.compile(r"\b(email|sophia\.eagent@gmail\.com)\b", re.I)
STANDALONE = re.compile(r"\b(standalone repo|standalone repository|open source on github)\b", re.I)
PR_ONLY = re.compile(r"\b(prs? (?:go|against|to)|open a pr|submit a pr|pull request)\b", re.I)
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
        if i == 0:
            return float(match.group(2))
        return float(match.group(1))
    return 0.0

def reward_from_body(body):
    patterns = [
        re.compile(r"\breward(?:_rtc)?\s*[:=]\s*\*{0,2}(\d+(?:\.\d+)?)\b", re.I),
        re.compile(r"\bpayout\s*[:=]\s*\*{0,2}(\d+(?:\.\d+)?)\s*RTC\b", re.I),
        re.compile(r"\b(\d+(?:\.\d+)?)\s*RTC\b", re.I),
    ]
    values = []
    for pattern in patterns:
        values += [float(x) for x in pattern.findall(body or "") if float(x) <= 1000]
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
    flags = []
    if SECURITY.search(text): flags.append("security-adjacent")
    if FUND.search(text): flags.append("fund-movement")
    if EXTERNAL.search(text): flags.append("external-publication/account")
    if HARDWARE.search(text): flags.append("hardware/user-presence")
    if EMAIL.search(text): route = "email-fallback"
    elif STANDALONE.search(text): route = "standalone"
    elif PR_ONLY.search(text): route = "pr-only"
    else: route = "comment-or-unspecified"
    return route, flags

def claim_signal_count(number):
    try:
        comments = api(f"/repos/{OWNER}/{REPO}/issues/{number}/comments", {"per_page":100})
    except Exception:
        return -1
    return sum(1 for comment in comments if CLAIM.search(comment.get("body") or ""))

def main():
    issues = []
    page = 1
    while page <= 15:
        batch = api(f"/repos/{OWNER}/{REPO}/issues", {"state":"open", "labels":"bounty", "per_page":100, "page":page})
        if not batch:
            break
        issues.extend(item for item in batch if "pull_request" not in item)
        if len(batch) < 100:
            break
        page += 1

    raw = []
    for issue in issues:
        title, body = issue.get("title", ""), issue.get("body") or ""
        reward = reward_from_title(title) or reward_from_body(body)
        if reward <= 0:
            continue
        route, flags = classify(body, title)
        raw.append((reward, issue, route, flags))
    raw.sort(key=lambda row: row[0], reverse=True)

    candidates = []
    for index, (reward, issue, route, flags) in enumerate(raw):
        claims = claim_signal_count(issue["number"]) if (reward >= 20 and index < 100) else -1
        comments = int(issue.get("comments") or 0)
        penalty = 0
        if "security-adjacent" in flags: penalty += 500
        if "fund-movement" in flags: penalty += 500
        if "external-publication/account" in flags: penalty += 120
        if "hardware/user-presence" in flags: penalty += 120
        if route == "pr-only": penalty += 35
        if claims > 0: penalty += min(80, claims * 8)
        if comments > 20: penalty += min(30, comments / 4)
        score = round(reward - penalty, 2)
        hard = {"security-adjacent", "fund-movement"} & set(flags)
        user_dep = {"external-publication/account", "hardware/user-presence"} & set(flags)
        if hard:
            decision = "EXCLUDE"
        elif user_dep:
            decision = "BLOCKED_USER_OR_EXTERNAL"
        elif route == "pr-only" and reward < 50:
            decision = "DEFER_ROUTE"
        elif claims >= 3:
            decision = "SATURATION_RECHECK"
        elif score >= 40:
            decision = "EXECUTE"
        elif score >= 15:
            decision = "VERIFY"
        else:
            decision = "DEFER"
        candidates.append(Candidate(issue["number"], title, issue["html_url"], reward, comments, claims, route, flags, score, decision))
        time.sleep(0.03)

    candidates.sort(key=lambda c: (c.decision == "EXECUTE", c.score, c.reward_rtc), reverse=True)
    output = {
        "source": f"https://github.com/{OWNER}/{REPO}/issues",
        "accounting_note": "Triage only. No item here is earned RTC.",
        "candidate_count": len(candidates),
        "candidates": [asdict(c) for c in candidates],
    }
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/rtc-candidate-queue.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    rows = ["# RTC Candidate Queue", "", "Triage only. Nothing here is earned RTC.", "", "| Decision | RTC | # | Route | Claim signals | Score | Title |", "|---|---:|---:|---|---:|---:|---|"]
    for candidate in candidates[:100]:
        rows.append(f"| {candidate.decision} | {candidate.reward_rtc:g} | [{candidate.number}]({candidate.url}) | {candidate.route} | {candidate.claim_signals} | {candidate.score:g} | {candidate.title.replace('|', '/')} |")
    Path("artifacts/rtc-candidate-queue.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"ranked {len(candidates)} bounties")
    print("top executable:")
    for candidate in [x for x in candidates if x.decision == "EXECUTE"][:10]:
        print(f"#{candidate.number}: {candidate.reward_rtc:g} RTC score={candidate.score:g} route={candidate.route} {candidate.title}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
