#!/usr/bin/env python3
"""Build a fail-closed cross-repository RTC opportunity queue.

Triage only. This script NEVER promotes accounting stages and NEVER treats
advertised RTC as earned. It discovers live RTC/bounty issues across Scottcjn-
owned repositories, detects reward drift, classifies route/safety constraints,
deduplicates our own economic lanes, and weights substantive competitor work
more heavily than claim chatter.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN", "")
UA = "prins1bap-ui-rtc-preflight-v2"
OWNER = "Scottcjn"
USER_LOGIN = "prins1bap-ui"

# Key by repository + issue number. Same-number issues in different repos are
# different economic lanes (for example Rustchain#29 vs rustchain-bounties#29).
OWN_WORK: set[tuple[str, int]] = {
    ("rustchain-bounties", 100), ("rustchain-bounties", 254),
    ("rustchain-bounties", 293), ("rustchain-bounties", 315),
    ("rustchain-bounties", 398), ("rustchain-bounties", 402),
    ("rustchain-bounties", 520), ("rustchain-bounties", 685),
    ("rustchain-bounties", 747), ("rustchain-bounties", 1102),
    ("rustchain-bounties", 13226), ("rustchain-bounties", 13954),
    ("rustchain-bounties", 14014), ("rustchain-bounties", 1524),
    ("rustchain-bounties", 1618), ("rustchain-bounties", 2143),
    ("rustchain-bounties", 2784), ("rustchain-bounties", 12442),
    ("rustchain-bounties", 12443), ("rustchain-bounties", 12444),
    ("rustchain-bounties", 16601), ("Rustchain", 29),
}

OFFENSIVE = re.compile(
    r"\b(red[- ]?team|exploit|vulnerab(?:ility|ility hunt)|bug bounty|security season|"
    r"adversarial|double[- ]?spend|auth bypass|privilege escalation|csrf|xss|rce|"
    r"break(?:ing)? security|replay attack)\b", re.I)
DEFENSIVE = re.compile(
    r"\b(harden|hardening|remediation|secure coding|validation|anti[- ]?spoof|"
    r"regression test|defensive|sanitize|least privilege|reliability)\b", re.I)
FUND = re.compile(
    r"\b(liquidity|tip(?:ping)?|donat(?:e|ion)|swap|bridge|escrow|staking?|x402|"
    r"send rtc|transfer rtc|funded wallet|real rtc|payment transaction)\b", re.I)
EXTERNAL = re.compile(
    r"\b(youtube|video post|article|blog|reddit|twitter|mastodon|dev\.to|medium|"
    r"hashnode|publication|ambassador|referral|hacker news|social media|subscriber|"
    r"discord|moltbook|crates\.io|npm publish|directory listing)\b", re.I)
HARDWARE = re.compile(
    r"\b(real hardware|physical hardware|powerpc|sparc|risc[- ]?v|mips|s390x|"
    r"mac os 9|amiga|dreamcast|raspberry pi|vintage hardware|run the miner|"
    r"run a full node|playtest|fps benchmark|hardware report)\b", re.I)
ELIGIBILITY = re.compile(
    r"\b(maintainer[- ]nominated|nomination required|invite[- ]only|invitation only|"
    r"selected contributors?|first[- ]right[- ]of[- ]claim|priority claimant|"
    r"pre[- ]approved|approved applicants?)\b", re.I)
MERGE_GATED = re.compile(
    r"\b(pay(?:s|ment)? on merge|payout on merge|rewarded on merge|must be merged|"
    r"merged pr required|merge required)\b", re.I)
PR_ROUTE = re.compile(
    r"\b(open|submit|send|create)\s+(?:a\s+)?(?:pull request|PR)\b|"
    r"\bPRs?\s+(?:go|against|to)\b|\bpull request to\b|\bdeliverable:\s*a PR\b", re.I)
STANDALONE_ROUTE = re.compile(
    r"\b(standalone repo|standalone repository|submit as standalone|"
    r"open source on github|public repository)\b", re.I)
EMAIL_ROUTE = re.compile(
    r"\b(sophia\.eagent@gmail\.com|submit by email|email submission|email the deliverable)\b", re.I)

INTENT_SIGNAL = re.compile(
    r"\b(claim(?:ing)?|i(?:'d| would) like to work|/apply|starting work|assign me)\b", re.I)
COMPLETED_SIGNAL = re.compile(
    r"\b(completed|implemented|submitted|delivered|ready for review|implementation complete|"
    r"pull request|PR\s*[:#]|PR submitted)\b", re.I)
AWARD_SIGNAL = re.compile(
    r"\b(accepted|approved|merged|awarded|queued|paid|payout queued|rewarded)\b", re.I)

TITLE_RANGE = re.compile(r"\b(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*RTC\b", re.I)
TITLE_UPTO = re.compile(r"\bup to\s+(\d+(?:\.\d+)?)\s*RTC\b", re.I)
RTC_VALUE = re.compile(r"\b(\d+(?:\.\d+)?)\s*RTC\b", re.I)
BODY_DIRECT = [
    re.compile(r"\b(?:reward|payout|bounty)\s*(?:amount)?\s*[:=]\s*\*{0,2}(\d+(?:\.\d+)?)\s*RTC\b", re.I),
    re.compile(r"^\s*#+\s+.*?\b(\d+(?:\.\d+)?)\s*RTC\b", re.I | re.M),
]
POOL_NEAR_VALUE = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*RTC\b.{0,24}\bpool\b|"
    r"\bpool\b.{0,24}\b(\d+(?:\.\d+)?)\s*RTC\b", re.I | re.S)


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


def repo_name_from_url(repository_url: str) -> str:
    return repository_url.rstrip("/").split("/")[-1]


def reward_from_title(title: str) -> float:
    match = TITLE_RANGE.search(title or "")
    if match:
        return max(float(match.group(1)), float(match.group(2)))
    match = TITLE_UPTO.search(title or "")
    if match:
        return float(match.group(1))
    match = RTC_VALUE.search(title or "")
    return float(match.group(1)) if match else 0.0


def reward_from_body(body: str) -> float:
    text = body or ""
    values: list[float] = []
    for pattern in BODY_DIRECT:
        for match in pattern.findall(text):
            value = float(match if isinstance(match, str) else next(x for x in match if x))
            if 0 < value <= 1000:
                values.append(value)
    # Early headings frequently contain the current reward when the issue title is stale.
    for line in text.splitlines()[:12]:
        if "pool" in line.lower():
            continue
        match = RTC_VALUE.search(line)
        if match:
            value = float(match.group(1))
            if 0 < value <= 1000:
                values.append(value)
                break
    return max(values, default=0.0)


@dataclass
class Competition:
    status: str
    intent_users: int = 0
    completed_users: int = 0
    maintainer_awards: int = 0
    comments_checked: int = 0


def competition(repo: str, number: int) -> Competition:
    try:
        comments = api(f"/repos/{OWNER}/{repo}/issues/{number}/comments", {"per_page": 100})
    except Exception:
        return Competition(status="unknown")
    stages: dict[str, int] = {}
    maintainer_awards = 0
    for comment in comments:
        login = ((comment.get("user") or {}).get("login") or "").strip()
        if not login or login.lower() == USER_LOGIN.lower():
            continue
        body = comment.get("body") or ""
        if login.lower() == OWNER.lower() and AWARD_SIGNAL.search(body):
            maintainer_awards += 1
        stage = 0
        if INTENT_SIGNAL.search(body):
            stage = 1
        if COMPLETED_SIGNAL.search(body):
            stage = 2
        if stage:
            stages[login.lower()] = max(stage, stages.get(login.lower(), 0))
    return Competition(
        status="ok",
        intent_users=sum(1 for stage in stages.values() if stage == 1),
        completed_users=sum(1 for stage in stages.values() if stage >= 2),
        maintainer_awards=maintainer_awards,
        comments_checked=len(comments),
    )


def discover_open_rtc_issues() -> list[dict]:
    """Discover across Scottcjn-owned repositories instead of one hardcoded repo."""
    seen: dict[tuple[str, int], dict] = {}
    queries = (
        f"user:{OWNER} is:issue is:open RTC",
        f"user:{OWNER} is:issue is:open bounty",
    )
    for query in queries:
        for page in range(1, 11):
            payload = api("/search/issues", {
                "q": query, "sort": "updated", "order": "desc",
                "per_page": 100, "page": page,
            })
            items = payload.get("items") or []
            for issue in items:
                repo = repo_name_from_url(issue.get("repository_url") or "")
                title = issue.get("title") or ""
                body = issue.get("body") or ""
                if not repo:
                    continue
                if "rtc" not in f"{title}\n{body}".lower() and "bounty" not in title.lower():
                    continue
                seen[(repo, int(issue["number"]))] = issue
            if len(items) < 100:
                break
            time.sleep(0.08)
    return list(seen.values())


def route_and_flags(repo: str, number: int, title: str, body: str) -> tuple[str, list[str]]:
    text = f"{title}\n{body}"
    flags: list[str] = []
    if (repo, number) in OWN_WORK:
        flags.append("existing-user-work")
    if ELIGIBILITY.search(text):
        flags.append("eligibility-gated")
    offensive = bool(OFFENSIVE.search(title))
    defensive = bool(DEFENSIVE.search(text))
    if offensive and not defensive:
        flags.append("offensive-security")
    elif defensive:
        flags.append("defensive-security")
    if FUND.search(text):
        flags.append("fund-movement")
    if EXTERNAL.search(text):
        flags.append("external-publication/account")
    if HARDWARE.search(text):
        flags.append("hardware/user-presence")
    if MERGE_GATED.search(text):
        flags.append("merge-gated")
    if POOL_NEAR_VALUE.search(text):
        flags.append("pool-or-program-reward")

    if EMAIL_ROUTE.search(text):
        route = "email-explicit"
    elif STANDALONE_ROUTE.search(text):
        route = "standalone"
    elif PR_ROUTE.search(text):
        route = "pr-only"
    elif repo == "rustchain-bounties":
        # Documented 403 fallback exists, but unspecified-route work still needs
        # final verification before the fallback can be assumed valid.
        route = "email-fallback-candidate"
    else:
        route = "unknown"
    if "merge-gated" in flags:
        route = "merge-gated"
    return route, flags


def effort_minutes(title: str, body: str) -> int:
    text = f"{title}\n{body}".lower()
    if any(word in text for word in ("mobile app", "browser extension", "full stack", "n64", "emulator")):
        return 360
    if any(word in text for word in ("integration", "sdk", "mcp server", "wallet", "miner client", "port ")):
        return 180
    if any(word in text for word in ("audit", "analysis", "research", "report", "documentation", "docs", "readme")):
        return 75
    if any(word in text for word in ("fix", "bug", "test", "script", "ci", "accessibility", "localization")):
        return 90
    return 120


def freshness_factor(updated_at: str | None) -> float:
    if not updated_at:
        return 0.75
    try:
        updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        age_days = max(0.0, (datetime.now(timezone.utc) - updated).total_seconds() / 86400)
    except Exception:
        return 0.75
    if age_days <= 14:
        return 1.0
    if age_days <= 45:
        return 0.9
    if age_days <= 120:
        return 0.75
    return 0.6


def route_factor(route: str) -> float:
    return {
        "standalone": 1.0, "email-explicit": 0.95,
        "email-fallback-candidate": 0.70, "unknown": 0.45,
        "pr-only": 0.20, "merge-gated": 0.08,
    }.get(route, 0.40)


def competition_factor(comp: Competition) -> float:
    if comp.status != "ok":
        return 0.55
    if comp.maintainer_awards:
        return 0.05
    if comp.completed_users >= 3:
        return 0.12
    if comp.completed_users == 2:
        return 0.22
    if comp.completed_users == 1:
        return 0.50
    if comp.intent_users >= 5:
        return 0.65
    if comp.intent_users >= 2:
        return 0.80
    return 1.0


@dataclass
class Candidate:
    repository: str
    number: int
    title: str
    url: str
    reward_title_rtc: float
    reward_body_rtc: float
    reward_rtc: float
    reward_conflict: bool
    comments: int
    competitor_intent: int
    competitor_completed: int
    maintainer_awards: int
    competition_status: str
    route: str
    flags: list[str]
    effort_minutes: int
    ev_index: float
    decision: str
    updated_at: str | None


def main() -> int:
    issues = discover_open_rtc_issues()
    preliminary: list[tuple] = []
    for issue in issues:
        repo = repo_name_from_url(issue.get("repository_url") or "")
        number = int(issue["number"])
        title = issue.get("title") or ""
        body = issue.get("body") or ""
        title_reward = reward_from_title(title)
        body_reward = reward_from_body(body)
        reward = max(title_reward, body_reward)
        if reward <= 0:
            continue
        conflict = title_reward > 0 and body_reward > 0 and abs(title_reward - body_reward) > 0.01
        route, flags = route_and_flags(repo, number, title, body)
        effort = effort_minutes(title, body)
        raw_priority = reward * route_factor(route) * freshness_factor(issue.get("updated_at")) / max(1.0, effort / 60)
        preliminary.append((raw_priority, issue, route, flags, title_reward, body_reward, conflict, effort))
    preliminary.sort(key=lambda row: row[0], reverse=True)

    candidates: list[Candidate] = []
    competition_budget = 160
    for index, (_, issue, route, flags, title_reward, body_reward, conflict, effort) in enumerate(preliminary):
        repo = repo_name_from_url(issue.get("repository_url") or "")
        number = int(issue["number"])
        title = issue.get("title") or ""
        reward = max(title_reward, body_reward)
        comp = competition(repo, number) if index < competition_budget else Competition(status="unknown")
        flagset = set(flags)
        factor = (
            route_factor(route) * competition_factor(comp) * freshness_factor(issue.get("updated_at"))
            * (0.70 if conflict else 1.0)
            * (0.75 if "pool-or-program-reward" in flagset else 1.0)
            * (0.75 if "defensive-security" in flagset else 1.0)
        )
        ev_index = round(reward * factor / max(1.0, effort / 60), 3)

        if "existing-user-work" in flagset:
            decision = "OWN_WORK_RECHECK"
        elif {"offensive-security", "fund-movement"} & flagset:
            decision = "EXCLUDE"
        elif {"eligibility-gated", "external-publication/account", "hardware/user-presence"} & flagset:
            decision = "BLOCKED_USER_OR_EXTERNAL"
        elif conflict:
            decision = "VERIFY_REWARD"
        elif comp.status != "ok":
            decision = "VERIFY_COMPETITION"
        elif comp.maintainer_awards or comp.completed_users >= 2:
            decision = "DEFER_SATURATED"
        elif route in {"merge-gated", "pr-only"}:
            decision = "DEFER_ROUTE"
        elif route == "unknown":
            decision = "VERIFY_ROUTE"
        elif "defensive-security" in flagset:
            decision = "VERIFY_SAFETY"
        elif comp.completed_users == 1:
            decision = "VERIFY_COMPETITION"
        elif "pool-or-program-reward" in flagset:
            decision = "VERIFY_REWARD"
        else:
            # Never blind-execute. Every survivor gets one final live inspection.
            decision = "FINAL_VERIFY"

        candidates.append(Candidate(
            repository=repo, number=number, title=title,
            url=issue.get("html_url") or "",
            reward_title_rtc=title_reward, reward_body_rtc=body_reward,
            reward_rtc=reward, reward_conflict=conflict,
            comments=int(issue.get("comments") or 0),
            competitor_intent=comp.intent_users,
            competitor_completed=comp.completed_users,
            maintainer_awards=comp.maintainer_awards,
            competition_status=comp.status, route=route, flags=flags,
            effort_minutes=effort, ev_index=ev_index, decision=decision,
            updated_at=issue.get("updated_at"),
        ))
        time.sleep(0.01)

    priority = {
        "FINAL_VERIFY": 10, "VERIFY_REWARD": 9, "VERIFY_ROUTE": 8,
        "VERIFY_COMPETITION": 7, "VERIFY_SAFETY": 6, "DEFER_ROUTE": 5,
        "DEFER_SATURATED": 4, "OWN_WORK_RECHECK": 3,
        "BLOCKED_USER_OR_EXTERNAL": 2, "EXCLUDE": 0,
    }
    candidates.sort(key=lambda item: (
        priority.get(item.decision, 1), item.ev_index, item.reward_rtc), reverse=True)

    generated_at = datetime.now(timezone.utc).isoformat()
    Path("artifacts").mkdir(exist_ok=True)
    payload = {
        "generated_at": generated_at,
        "source": f"GitHub issue search across {OWNER}-owned repositories",
        "accounting_note": "Triage only. No item here is earned, submitted, accepted, or received RTC.",
        "candidate_count": len(candidates),
        "final_verify_count": sum(1 for item in candidates if item.decision == "FINAL_VERIFY"),
        "candidates": [asdict(candidate) for candidate in candidates],
    }
    Path("artifacts/rtc-candidate-queue.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# RTC Candidate Queue", "", f"Generated: `{generated_at}`", "",
        "Triage only. `FINAL_VERIFY` still requires live authoritative inspection before work.", "",
        "| Decision | EV index | RTC | Repo/# | Route | Competitors I/C/A | Effort | Reward source | Title |",
        "|---|---:|---:|---|---|---:|---:|---|---|",
    ]
    for candidate in candidates[:200]:
        safe_title = candidate.title.replace("|", "/")
        reward_source = (
            f"title {candidate.reward_title_rtc:g} / body {candidate.reward_body_rtc:g}"
            if candidate.reward_conflict else
            ("body" if candidate.reward_body_rtc > candidate.reward_title_rtc else "title")
        )
        lines.append(
            f"| {candidate.decision} | {candidate.ev_index:g} | {candidate.reward_rtc:g} | "
            f"[{candidate.repository}#{candidate.number}]({candidate.url}) | {candidate.route} | "
            f"{candidate.competitor_intent}/{candidate.competitor_completed}/{candidate.maintainer_awards} | "
            f"{candidate.effort_minutes}m | {reward_source} | {safe_title} |"
        )
    Path("artifacts/rtc-candidate-queue.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"ranked {len(candidates)} RTC candidates across Scottcjn-owned repositories")
    for candidate in [item for item in candidates if item.decision == "FINAL_VERIFY"][:20]:
        print(
            f"FINAL_VERIFY {candidate.repository}#{candidate.number}: "
            f"{candidate.reward_rtc:g} RTC ev={candidate.ev_index:g} route={candidate.route} "
            f"completed_competitors={candidate.competitor_completed} {candidate.title}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
