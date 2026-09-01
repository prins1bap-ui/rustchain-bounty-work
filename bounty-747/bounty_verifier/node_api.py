from __future__ import annotations

import json
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from .core import Check


class NodeAPI:
    def __init__(self, base_url: str) -> None:
        p = urlparse(base_url)
        if p.scheme != "https" or not p.hostname:
            raise ValueError("RUSTCHAIN_NODE_URL must be an https URL")
        self.base_url = base_url.rstrip("/")

    def wallet_exists(self, wallet: str) -> Check:
        url = f"{self.base_url}/wallet/balance?miner_id={quote(wallet)}"
        try:
            req = Request(url, headers={"User-Agent": "rtc-bounty-verifier/1.0"})
            with urlopen(req, timeout=10) as r:
                payload = json.load(r)
        except Exception as exc:
            return Check("unknown", f"node query failed: {type(exc).__name__}")
        if not isinstance(payload, dict):
            return Check("unknown", "unexpected node response")
        if payload.get("error") or payload.get("found") is False:
            return Check("fail", "wallet/miner ID not found")
        balance = payload.get("balance_rtc", payload.get("balance"))
        if balance is None:
            return Check("pass", "wallet/miner ID resolved")
        return Check("pass", f"wallet/miner ID resolved; reported balance {balance} RTC")
