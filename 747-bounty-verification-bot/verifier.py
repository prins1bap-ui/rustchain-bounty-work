#!/usr/bin/env python3
"""Read-only RustChain bounty claim verifier for bounty #747.

No payments, transfers, wallet writes, or claim mutations are performed.
The only optional write action is posting a payout-inert diagnostic comment to GitHub.
"""
from __future__ import annotations

import argparse
import html
import ipaddress
import json
import os
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from typing import Iterable, Optional

UA = "rustchain-bounty-verifier/1.2 (+https://github.com/prins1bap-ui/rustchain-bounty-work)"
DEFAULT_NODE = "https://rustchain.org"
MAX_PROOF_BYTES = 1_000_000
MAX_REDIRECTS = 3
PROOF_TIMEOUT = 8
ALLOWED_PROOF_HOSTS = {"dev.to", "www.dev.to", "medium.com", "www.medium.com"}
TRUSTED_PAYOUT_ACTORS = {"scottcjn", "sophiaeagent-beep", "autojanitor"}
STRUCTURED_PAYOUT_RE = re.compile(
    r"(?im)(?:<!--\s*rustchain-payout\b[^>]*-->|"
    r"\b(?:pending_id|transfer_id|txid)\s*[:=#]\s*[A-Za-z0-9._:-]+|"
    r"\b(?:rtc-paid|payout-status)\s*:\s*(?:paid|queued|pending|settled)\b)"
)

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
    diagnostic_score: int

    @property
    def suggested_rtc(self) -> int:
        """Backward-compatible internal value only; never authoritative for payout."""
        return self.diagnostic_score

    def to_json(self) -> str:
        return json.dumps({
            "claimant": self.claimant,
            "wallet": self.wallet,
            "checks": [asdict(c) for c in self.checks],
            "diagnostic_score": self.diagnostic_score,
            "payout_authority": False,
            "ignore_for_payout": True,
        }, indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        rows = []
        for c in self.checks:
            icon = "✅" if c.ok is True else "❌" if c.ok is False else "⚪"
            rows.append(f"| {c.name} | {icon} {c.detail} |")
        return (
            f"## Automated diagnostic for @{self.claimant}\n\n"
            "**PAYOUT-INERT: DO NOT USE OR PARSE THIS COMMENT TO AUTHORIZE, QUEUE, OR CALCULATE RTC.** "
            "Human maintainer adjudication is the only payout authority.\n\n"
            "| Check | Result |\n|---|---|\n" + "\n".join(rows) +
            f"\n\n**Diagnostic completeness score (not RTC, not a payout):** {self.diagnostic_score}/75\n\n"
            "> Read-only diagnostic only. This bot never approves or executes payment."
        )


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
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError):
        return None, {}, b""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _public_ips_for_host(host: str) -> bool:
    """Return True only when every resolved address is globally routable."""
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except OSError:
        return False
    ips = {info[4][0] for info in infos if info and info[4]}
    if not ips:
        return False
    for raw in ips:
        try:
            ip = ipaddress.ip_address(raw.split("%", 1)[0])
        except ValueError:
            return False
        if not ip.is_global:
            return False
    return True


def _validated_proof_url(url: str) -> Optional[str]:
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return None
    if parsed.scheme.lower() not in ("http", "https"):
        return None
    if parsed.username or parsed.password or parsed.port not in (None, 80, 443):
        return None
    host = (parsed.hostname or "").rstrip(".").lower()
    if host not in ALLOWED_PROOF_HOSTS:
        return None
    if not _public_ips_for_host(host):
        return None
    return urllib.parse.urlunsplit(parsed)


def _proof_fetch(url: str, method: str = "GET", max_bytes: int = MAX_PROOF_BYTES):
    """Fetch an allowlisted public proof URL with redirect re-validation and a hard body cap."""
    current = url
    opener = urllib.request.build_opener(_NoRedirect)
    for _ in range(MAX_REDIRECTS + 1):
        safe = _validated_proof_url(current)
        if not safe:
            return None, {}, b"", "blocked unsafe or non-allowlisted URL"
        req = urllib.request.Request(safe, headers={"User-Agent": UA}, method=method)
        try:
            with opener.open(req, timeout=PROOF_TIMEOUT) as response:
                status = response.status
                headers = response.headers
                if 300 <= status < 400:
                    location = headers.get("Location")
                    if not location:
                        return status, headers, b"", "redirect missing Location"
                    current = urllib.parse.urljoin(safe, location)
                    continue
                if method == "HEAD":
                    return status, headers, b"", None
                declared = headers.get("Content-Length")
                if declared:
                    try:
                        if int(declared) > max_bytes:
                            return status, headers, b"", "response too large"
                    except ValueError:
                        pass
                body = response.read(max_bytes + 1)
                if len(body) > max_bytes:
                    return status, headers, b"", "response too large"
                return status, headers, body, None
        except urllib.error.HTTPError as e:
            if 300 <= e.code < 400:
                location = e.headers.get("Location")
                if not location:
                    return e.code, e.headers, b"", "redirect missing Location"
                current = urllib.parse.urljoin(safe, location)
                continue
            return e.code, e.headers, b"", None
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError):
            return None, {}, b"", "network error"
    return None, {}, b"", "too many redirects"


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
        try:
            items = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return Check(f"{owner} repos starred", None, "Unable to verify (malformed GitHub response)"), count
        if not isinstance(items, list):
            return Check(f"{owner} repos starred", None, "Unable to verify (unexpected GitHub response)"), count
        count += sum(1 for x in items if isinstance(x, dict) and (x.get("owner") or {}).get("login", "").lower() == owner.lower())
        if len(items) < 100:
            break
    return Check(f"{owner} repos starred", count > 0, str(count)), count


def wallet_exists(wallet: Optional[str], node_url: str) -> Check:
    if not wallet:
        return Check("Wallet existence", None, "No wallet found in claim")
    base = node_url.rstrip("/")
    q = urllib.parse.urlencode({"miner_id": wallet})
    candidates = [f"{base}/wallet/balance?{q}", f"{base}/api/wallet/balance?{q}"]
    statuses = []
    for url in candidates:
        status, _, body = _request(url, timeout=8)
        statuses.append(status)
        if status == 200:
            try:
                data = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return Check("Wallet existence", None, "Indeterminate: malformed wallet response")
            if not isinstance(data, dict):
                return Check("Wallet existence", None, "Indeterminate: unexpected wallet response")
            if data.get("ok") is False:
                continue
            bal = data.get("balance", data.get("rtc_balance", data.get("amount")))
            has_identity = any(k in data for k in ("miner_id", "wallet", "wallet_id"))
            if bal is None and not has_identity:
                return Check("Wallet existence", None, "Indeterminate: no recognized wallet fields")
            return Check("Wallet existence", True, "Exists" + (f"; balance={bal}" if bal is not None else ""))
        if status not in (400, 404):
            return Check("Wallet existence", None, f"Indeterminate: wallet endpoint HTTP {status}")
    return Check("Wallet existence", False, f"Not found (HTTP {statuses[-1] if statuses else None})")


def url_liveness(url: Optional[str]) -> Check:
    if not url:
        return Check("Proof URL", None, "No proof URL found")
    if not _validated_proof_url(url):
        return Check("Proof URL", False, "URL must be a public dev.to or medium.com HTTP(S) URL")
    status, _, _, error = _proof_fetch(url, method="HEAD", max_bytes=0)
    if status in (405, 403) or (status is not None and status >= 500):
        status, _, _, error = _proof_fetch(url, method="GET", max_bytes=64_000)
    if error:
        return Check("Proof URL", None, f"Indeterminate: {error}")
    return Check("Proof URL", status is not None and 200 <= status < 400, f"HTTP {status}")


def article_word_count(url: Optional[str]) -> Check:
    if not url:
        return Check("Article word count", None, "No article URL found")
    if not _validated_proof_url(url):
        return Check("Article word count", False, "URL must be a public dev.to or medium.com URL")
    status, _, body, error = _proof_fetch(url, method="GET")
    if error:
        return Check("Article word count", None, f"Indeterminate: {error}")
    if status != 200:
        return Check("Article word count", False, f"HTTP {status}")
    try:
        text = body.decode("utf-8", "replace")
        text = re.sub(r"<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>", " ", text, flags=re.I|re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(text)
        words = re.findall(r"\b[\w’'-]+\b", text)
    except Exception:
        return Check("Article word count", None, "Indeterminate: content parsing failed")
    n = len(words)
    return Check("Article word count", n >= 500, f"~{n} words")


def prior_payment_markers(comments: Iterable[dict], claimant: str, wallet: Optional[str]) -> Check:
    claimant_l = claimant.lower()
    wallet_l = wallet.lower() if wallet else None
    hits = []
    for c in comments:
        body = (c.get("body") or "")
        user = ((c.get("user") or {}).get("login") or "").lower()
        if user not in TRUSTED_PAYOUT_ACTORS:
            continue
        body_l = body.lower()
        references_person = f"@{claimant_l}" in body_l or (wallet_l and wallet_l in body_l)
        if references_person and STRUCTURED_PAYOUT_RE.search(body):
            hits.append(c.get("html_url") or c.get("url") or "trusted structured comment")
    if hits:
        return Check("Prior payment markers", False, f"Found {len(hits)} trusted structured payout marker(s)")
    return Check("Prior payment markers", True, "No trusted structured payout marker found in supplied history")


def parse_claim(text: str) -> tuple[Optional[str], Optional[str]]:
    urls = re.findall(r"https?://[^\s>)\]]+", text or "")
    proof = urls[0].rstrip(".,") if urls else None
    wallet = None
    m = re.search(r"\bRTC[a-fA-F0-9]{40}\b", text or "")
    if m:
        wallet = m.group(0)
    else:
        m = re.search(r"(?im)^\s*(?:rtc\s+wallet|wallet|miner_id)\s*:\s*`?([^\s`]+)", text or "")
        if m:
            wallet = m.group(1).strip()
    return wallet, proof


def _safe_check(name: str, fn) -> Check:
    try:
        return fn()
    except Exception as exc:
        return Check(name, None, f"Indeterminate: verifier error ({type(exc).__name__})")


def verify(user: str, claim_text: str, token: Optional[str], comments: list[dict], node_url: str,
           target: str = "Scottcjn") -> Verification:
    wallet, proof = parse_claim(claim_text)
    c_follow = _safe_check("Follows @" + target, lambda: follows_target(user, target, token))
    try:
        c_stars, _ = count_owner_stars(user, target, token)
    except Exception as exc:
        c_stars = Check(f"{target} repos starred", None, f"Indeterminate: verifier error ({type(exc).__name__})")
    c_wallet = _safe_check("Wallet existence", lambda: wallet_exists(wallet, node_url))
    c_url = _safe_check("Proof URL", lambda: url_liveness(proof))
    c_words = _safe_check("Article word count", lambda: article_word_count(proof))
    c_dup = _safe_check("Prior payment markers", lambda: prior_payment_markers(comments, user, wallet))
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
