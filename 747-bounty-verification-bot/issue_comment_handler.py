#!/usr/bin/env python3
"""GitHub issue_comment event adapter for RustChain bounty #747.

The adapter verifies claim-like comments and may post one verification comment.
It never performs RTC transfers, signing, wallet writes, escrow, settlement, or payout actions.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

from verifier import verify

KEYWORDS = ("claiming", "wallet:", "rtc wallet:", "miner_id:", "submitted", "/claim")
BOT_MARKER = "<!-- rustchain-bounty-verifier -->"


def should_process(body: str, sender_type: str = "User") -> bool:
    text = (body or "").lower()
    if sender_type.lower() == "bot" or BOT_MARKER in (body or ""):
        return False
    return any(keyword in text for keyword in KEYWORDS)


def load_event(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def github_json(url: str, token: str, method: str = "GET", payload=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "rustchain-bounty-verifier/1.1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read()
        return json.loads(body.decode("utf-8")) if body else None


def fetch_all_comments(api_url: str, token: str) -> list[dict]:
    comments = []
    page = 1
    while True:
        separator = "&" if "?" in api_url else "?"
        batch = github_json(f"{api_url}{separator}per_page=100&page={page}", token)
        if not isinstance(batch, list):
            return comments
        comments.extend(batch)
        if len(batch) < 100:
            return comments
        page += 1


def run(event: dict, token: str, node_url: str) -> int:
    comment = event.get("comment") or {}
    body = comment.get("body") or ""
    sender_type = ((comment.get("user") or {}).get("type") or "User")
    if not should_process(body, sender_type):
        print("No claim-like comment; skipping.")
        return 0

    claimant = ((comment.get("user") or {}).get("login") or "").strip()
    comments_url = (event.get("issue") or {}).get("comments_url")
    if not claimant or not comments_url:
        raise ValueError("Event is missing claimant login or issue comments_url")

    history = fetch_all_comments(comments_url, token)
    result = verify(claimant, body, token, history, node_url)

    source_id = str(comment.get("id") or "")
    dedupe_marker = f"<!-- source-comment:{source_id} -->" if source_id else ""
    if dedupe_marker and any(dedupe_marker in (item.get("body") or "") for item in history):
        print("Verification for this source comment already exists; skipping.")
        return 0

    rendered = BOT_MARKER + "\n" + result.to_markdown()
    if dedupe_marker:
        rendered += "\n" + dedupe_marker
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
    return run(load_event(event_path), token, node_url)


if __name__ == "__main__":
    raise SystemExit(main())
