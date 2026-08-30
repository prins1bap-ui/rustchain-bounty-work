#!/usr/bin/env python3
"""Read-only RustChain bounty claim verifier for bounty #747.

No payments, transfers, wallet writes, or claim mutations are performed.
The only optional write action is posting a verification comment to GitHub.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from typing import Iterable, Optional

UA = "rustchain-bounty-verifier/1.0 (+https://github.com/prins1bap-ui/rustchain-bounty-work)"
DEFAULT_NODE = "https://rustchain.org"
PAID_KEYS = ("paid", "queued", "payout", "pending_id", "transaction", "txid", "settled")

@dataclass
class Check:
    name: str
    ok: Optional[bool]
    detail: str

@dataclass
class Verification:
    claimant: str
    wallet: Optional[str]
    checks: list[Check]
    suggested_rtc: int

    def to_json(self) -> str:
        return json.dumps({"claimant": self.claimant, "wallet": self.wallet,
                           "checks": [asdict(c) for c in self.checks],
                           "suggested_rtc": self.suggested_rtc}, indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        rows = []
        for c in self.checks:
            icon = "✅" if c.ok is True else "❌" if c.ok is False else "⚪"
            rows.append(f"| {c.name} | {icon} {c.detail} |")
        return (f"## Automated Verification for @{self.claimant}\n\n"
                "| Check | Result |\n|---|---|\n" + "\n".join(rows) +
                f"\n\n**Suggested payout basis:** {self.suggested_rtc} RTC\n\n"
                "> Read-only verification only. Human maintainer approval is required; this bot never executes payment.")


def _request(url: str, token: Optional[str] = None, method: str = "GET", timeout: int = 15):
    headers = {"User-Agent": UA, "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


def follows_target(user: str, target: str, token: Optional[str]) -> Check:
    url = f"https://api.github.com/users/{urllib.parse.quote(user)}/following/{urllib.parse.quote(target)}"
    status, _, _ = _request(url, token)
    if status == 204:
        return Check("Follows @" + target, True, "Yes")
    if status == 404:
        return Check("Follows @" + target, False, "No")
    return Check("Follows @" + target, None, f"Unable to verify (HTTP {status})")


def count_owner_stars(user: str, owner: str, token: Optional[str], max_pages: int = 10) -> tuple[Check, int]:
    count = 0
    for page in range(1, max_pages + 1):
        url = f"https://api.github.com/users/{urllib.parse.quote(user)}/starred?per_page=100&page={page}"
        status, _, body = _request(url, token)
        if status != 200:
            return Check(f"{owner} repos starred", None, f"Unable to verify (HTTP {status})"), count
        items = json.loads(body.decode("utf-8"))
        count += sum(1 for x in items if (x.get("owner") or {}).get("login", "").lower() == owner.lower())
        if len(items) < 100:
            break
    return Check(f"{owner} repos starred", count > 0, str(count)), count


def wallet_exists(wallet: Optional[str], node_url: str) -> Check:
    if not wallet:
        return Check("Wallet existence", None, "No wallet found in claim")
    base = node_url.rstrip("/")
    q = urllib.parse.urlencode({"miner_id": wallet})
    candidates = [f"{base}/wallet/balance?{q}", f"{base}/api/wallet/balance?{q}"]
    last = None
    for url in candidates:
        status, _, body = _request(url)
        last = status
        if status == 200:
            text = body.decode("utf-8", "replace")
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    if data.get("ok") is False:
                        continue
                    bal = data.get("balance", data.get("rtc_balance", data.get("amount")))
                    return Check("Wallet existence", True, f"Exists" + (f"; balance={bal}" if bal is not None else ""))
            except json.JSONDecodeError:
                pass
            return Check("Wallet existence", True, "Endpoint returned 200")
        if status in (400, 404):
            continue
    return Check("Wallet existence", False if last in (400,404) else None, f"Not verified (HTTP {last})")


def url_liveness(url: Optional[str]) -> Check:
    if not url:
        return Check("Proof URL", None, "No proof URL found")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return Check("Proof URL", False, "Unsupported URL scheme")
    status, _, _ = _request(url, method="HEAD")
    if status in (405, 403) or status >= 500:
        status, _, _ = _request(url, method="GET")
    return Check("Proof URL", 200 <= status < 400, f"HTTP {status}")


def article_word_count(url: Optional[str]) -> Check:
    if not url:
        return Check("Article word count", None, "No article URL found")
    host = urllib.parse.urlparse(url).netloc.lower()
    if not any(d in host for d in ("dev.to", "medium.com")):
        return Check("Article word count", None, "Not a Dev.to/Medium URL")
    status, _, body = _request(url)
    if status != 200:
        return Check("Article word count", False, f"HTTP {status}")
    text = body.decode("utf-8", "replace")
    text = re.sub(r"<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>", " ", text, flags=re.I|re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    words = re.findall(r"\b[\w’'-]+\b", text)
    n = len(words)
    return Check("Article word count", n >= 500, f"~{n} words")


def prior_payment_markers(comments: Iterable[dict], claimant: str, wallet: Optional[str]) -> Check:
    claimant_l = claimant.lower()
    wallet_l = wallet.lower() if wallet else None
    hits = []
    for c in comments:
        body = (c.get("body") or "").lower()
        user = ((c.get("user") or {}).get("login") or "").lower()
        references_person = user == claimant_l or f"@{claimant_l}" in body or (wallet_l and wallet_l in body)
        if references_person and any(k in body for k in PAID_KEYS):
            hits.append(c.get("html_url") or c.get("url") or "comment")
    if hits:
        return Check("Prior payment markers", False, f"Found {len(hits)} possible prior payout marker(s)")
    return Check("Prior payment markers", True, "No matching payout marker found in supplied history")


def parse_claim(text: str) -> tuple[Optional[str], Optional[str]]:
    urls = re.findall(r"https?://[^\s>)\]]+", text)
    proof = urls[0].rstrip(".,") if urls else None
    wallet = None
    m = re.search(r"\bRTC[a-fA-F0-9]{40}\b", text)
    if m:
        wallet = m.group(0)
    else:
        m = re.search(r"(?im)^\s*(?:rtc\s+wallet|wallet|miner_id)\s*:\s*`?([^\s`]+)", text)
        if m:
            wallet = m.group(1).strip()
    return wallet, proof


def verify(user: str, claim_text: str, token: Optional[str], comments: list[dict], node_url: str,
           target: str = "Scottcjn") -> Verification:
    wallet, proof = parse_claim(claim_text)
    c_follow = follows_target(user, target, token)
    c_stars, _ = count_owner_stars(user, target, token)
    c_wallet = wallet_exists(wallet, node_url)
    c_url = url_liveness(proof)
    c_words = article_word_count(proof)
    c_dup = prior_payment_markers(comments, user, wallet)
    score = 0
    if c_follow.ok is True and c_stars.ok is True: score += 30
    if c_wallet.ok is True: score += 10
    if c_url.ok is True: score += 10
    if c_words.ok is True: score += 10
    if c_dup.ok is True: score += 15
    return Verification(user, wallet, [c_follow, c_stars, c_wallet, c_url, c_words, c_dup], score)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Read-only RustChain bounty claim verifier")
    p.add_argument("--user", required=True)
    p.add_argument("--claim-text", required=True)
    p.add_argument("--comments-json", help="Path to JSON array of prior comments")
    p.add_argument("--node-url", default=os.environ.get("RUSTCHAIN_NODE_URL", DEFAULT_NODE))
    p.add_argument("--github-token", default=os.environ.get("GITHUB_TOKEN"))
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    comments = []
    if args.comments_json:
        with open(args.comments_json, "r", encoding="utf-8") as f:
            comments = json.load(f)
    result = verify(args.user, args.claim_text, args.github_token, comments, args.node_url)
    print(result.to_json() if args.json else result.to_markdown())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
