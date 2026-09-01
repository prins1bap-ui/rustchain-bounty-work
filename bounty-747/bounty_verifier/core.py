from __future__ import annotations

import ipaddress
import json
import re
import socket
from dataclasses import dataclass, asdict
from html.parser import HTMLParser
from typing import Iterable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ALLOWED_ARTICLE_HOSTS = {"dev.to", "medium.com", "hashnode.com"}
PAID_RE = re.compile(r"\b(paid|payment|payout|earned|approved|accepted|pending_id|tx_hash)\b", re.I)
WALLET_RE = re.compile(r"\bRTC[a-fA-F0-9]{40}\b")
URL_RE = re.compile(r"https?://[^\s)>\]]+")


@dataclass
class Check:
    status: str
    detail: str


@dataclass
class Verification:
    claimant: str
    follows_target: Check
    starred_repos: Check
    wallet: Check
    article: Check
    duplicate: Check

    def json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "nav", "footer"}:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "nav", "footer"} and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def extract_wallet(text: str) -> str | None:
    m = WALLET_RE.search(text or "")
    return m.group(0) if m else None


def extract_article_url(text: str) -> str | None:
    for raw in URL_RE.findall(text or ""):
        url = raw.rstrip(".,;:")
        host = (urlparse(url).hostname or "").lower()
        if host in ALLOWED_ARTICLE_HOSTS or host.endswith(".hashnode.dev"):
            return url
    return None


def is_public_http_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"}:
        return False
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except OSError:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            return False
    return True


def article_word_count(url: str, timeout: int = 10) -> Check:
    host = (urlparse(url).hostname or "").lower()
    if not (host in ALLOWED_ARTICLE_HOSTS or host.endswith(".hashnode.dev")):
        return Check("fail", "unsupported article host")
    if not is_public_http_url(url):
        return Check("fail", "URL did not resolve to a public HTTP(S) target")
    try:
        req = Request(url, headers={"User-Agent": "rtc-bounty-verifier/1.0"})
        with urlopen(req, timeout=timeout) as r:
            final = r.geturl()
            if not is_public_http_url(final):
                return Check("fail", "redirected to non-public target")
            body = r.read(2_000_000).decode("utf-8", "replace")
    except Exception as exc:
        return Check("unknown", f"article fetch failed: {type(exc).__name__}")
    parser = TextExtractor()
    parser.feed(body)
    words = re.findall(r"\b[\w'-]+\b", " ".join(parser.parts))
    return Check("pass", f"live article; approximately {len(words)} visible words")


def duplicate_payment_check(prior_comments: Iterable[str], claimant: str) -> Check:
    claimant_l = claimant.lower().lstrip("@")
    hits = []
    for body in prior_comments:
        low = (body or "").lower()
        if claimant_l in low and PAID_RE.search(body or ""):
            hits.append((body or "").strip().replace("\n", " ")[:180])
    if hits:
        return Check("review", f"possible prior payout evidence: {hits[0]}")
    return Check("pass", "no explicit prior payout evidence found for claimant")


def markdown(v: Verification) -> str:
    rows = [
        ("Follows target", v.follows_target),
        ("Starred repos", v.starred_repos),
        ("Wallet", v.wallet),
        ("Article", v.article),
        ("Duplicate claim", v.duplicate),
    ]
    out = [f"## Automated Verification for @{v.claimant}", "", "| Check | Status | Detail |", "|---|---|---|"]
    for name, check in rows:
        out.append(f"| {name} | {check.status} | {check.detail.replace('|', '/')} |")
    out += ["", "Verification only. Human approval is required for any payout."]
    return "\n".join(out)
