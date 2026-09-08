#!/usr/bin/env python3
"""GitHub issue_comment event adapter for RustChain bounty #747.

The adapter verifies claim-like comments and may post one payout-inert diagnostic comment.
It never performs RTC transfers, signing, wallet writes, escrow, settlement, or payout actions.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys
import urllib.request

from verifier import verify

KEYWORDS = ("claiming", "wallet:", "rtc wallet:", "miner_id:", "submitted", "/claim")
BOT_MARKER = "<!-- rustchain-bounty-verifier -->"
PAYOUT_IGNORE_MARKER = "<!-- rtc-payout-ignore:true -->"
USER_MARKER_PREFIX = "<!-- verifier-user:"
SOURCE_MARKER_PREFIX = "<!-- source-comment:"
USER_THROTTLE_SECONDS = 900
ISSUE_BURST_WINDOW_SECONDS = 3600
ISSUE_BURST_LIMIT = 20


def should_process(body: str, sender_type: str = "User") -> bool:
    text = (body or "").lower()
    if sender_type.lower() == "bot" or BOT_MARKER in (body or ""):
        return False
    return any(keyword in text for keyword in KEYWORDS)


def load_event(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        event = json.load(handle)
    if not isinstance(event, dict):
        raise ValueError("GitHub event payload must be an object")
    return event


def github_json(url: str, token: str, method: str = "GET", payload=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "rustchain-bounty-verifier/1.2",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=15) as response:
        body = response.read(1_000_001)
        if len(body) > 1_000_000:
            raise ValueError("GitHub response too large")
        return json.loads(body.decode("utf-8")) if body else None


def fetch_all_comments(api_url: str, token: str, max_pages: int = 20) -> list[dict]:
    comments = []
    for page in range(1, max_pages + 1):
        separator = "&" if "?" in api_url else "?"
        batch = github_json(f"{api_url}{separator}per_page=100&page={page}", token)
        if not isinstance(batch, list):
            raise ValueError("GitHub comments response was not a list")
        comments.extend(item for item in batch if isinstance(item, dict))
        if len(batch) < 100:
            return comments
    return comments


def _parse_github_time(value: str | None):
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _claim_hash(body: str) -> str:
    return hashlib.sha256((body or "").encode("utf-8")).hexdigest()[:16]


def _source_marker(comment_id: str, body: str) -> str:
    return f"{SOURCE_MARKER_PREFIX}{comment_id};sha256:{_claim_hash(body)} -->"


def _user_marker(claimant: str) -> str:
    safe = "".join(ch for ch in claimant.lower() if ch.isalnum() or ch in "-_")
    return f"{USER_MARKER_PREFIX}{safe} -->"


def throttle_reason(history: list[dict], claimant: str, now: dt.datetime | None = None) -> str | None:
    now = now or dt.datetime.now(dt.timezone.utc)
    user_marker = _user_marker(claimant)
    issue_recent = 0
    for item in history:
        body = item.get("body") or ""
        if BOT_MARKER not in body:
            continue
        created = _parse_github_time(item.get("created_at"))
        if not created:
            continue
        age = (now - created).total_seconds()
        if age < 0:
            age = 0
        if user_marker in body and age < USER_THROTTLE_SECONDS:
            return "per-user/per-issue throttle active"
        if age < ISSUE_BURST_WINDOW_SECONDS:
            issue_recent += 1
    if issue_recent >= ISSUE_BURST_LIMIT:
        return "issue-wide bot reply throttle active"
    return None


def run(event: dict, token: str, node_url: str) -> int:
    action = (event.get("action") or "").lower()
    if action and action not in {"created", "edited"}:
        print(f"Unsupported issue_comment action {action!r}; skipping.")
        return 0

    comment = event.get("comment")
    issue = event.get("issue")
    if not isinstance(comment, dict) or not isinstance(issue, dict):
        raise ValueError("Event is missing comment or issue object")
    body = comment.get("body")
    if not isinstance(body, str):
        raise ValueError("Event comment body must be text")
    sender_type = ((comment.get("user") or {}).get("type") or "User")
    if not should_process(body, sender_type):
        print("No claim-like comment; skipping.")
        return 0

    claimant = ((comment.get("user") or {}).get("login") or "").strip()
    comments_url = issue.get("comments_url")
    if not claimant or not isinstance(comments_url, str) or not comments_url.startswith("https://api.github.com/repos/"):
        raise ValueError("Event is missing a valid claimant login or issue comments_url")

    history = fetch_all_comments(comments_url, token)
    source_id = str(comment.get("id") or "")
    if not source_id:
        raise ValueError("Event comment id is required for idempotency")

    exact_marker = _source_marker(source_id, body)
    if any(exact_marker in (item.get("body") or "") for item in history):
        print("Verification for this source comment revision already exists; skipping.")
        return 0

    reason = throttle_reason(history, claimant)
    if reason:
        print(f"{reason}; skipping diagnostic reply.")
        return 0

    result = verify(claimant, body, token, history, node_url)
    rendered = (
        BOT_MARKER + "\n" +
        PAYOUT_IGNORE_MARKER + "\n" +
        _user_marker(claimant) + "\n" +
        exact_marker + "\n" +
        result.to_markdown()
    )
    github_json(comments_url, token, method="POST", payload={"body": rendered})
    print(rendered)
    return 0


def main() -> int:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    token = os.environ.get("GITHUB_TOKEN")
    node_url = os.environ.get("RUSTCHAIN_NODE_URL", "https://rustchain.org")
    if not event_path or not token:
        print("GITHUB_EVENT_PATH and GITHUB_TOKEN are required", file=sys.stderr)
        return 2
    try:
        return run(load_event(event_path), token, node_url)
    except Exception as exc:
        print(f"Verifier adapter failed closed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
