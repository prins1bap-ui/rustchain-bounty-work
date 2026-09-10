"""LangChain-compatible RustChain read-only tool.

Bounty #3074 reference implementation. Uses only public, read-only endpoints.
"""
from __future__ import annotations

from typing import Any, Literal
import requests

try:
    from langchain_core.tools import BaseTool
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover
    raise ImportError("Install langchain-core and pydantic to use RustChainTool") from exc


class RustChainInput(BaseModel):
    action: Literal["check_balance", "list_bounties", "get_node_health", "get_current_epoch"] = Field(...)
    wallet_id: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


class RustChainTool(BaseTool):
    """Read public RustChain state from a LangChain agent."""

    name: str = "rustchain"
    description: str = (
        "Read RustChain public state. Actions: check_balance, list_bounties, "
        "get_node_health, get_current_epoch. Never signs or sends transactions."
    )
    args_schema: type[BaseModel] = RustChainInput
    base_url: str = "https://rustchain.org"
    timeout_seconds: float = 15.0

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = requests.get(f"{self.base_url.rstrip('/')}{path}", params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    def check_balance(self, wallet_id: str) -> float:
        if not wallet_id:
            raise ValueError("wallet_id is required")
        data = self._get("/wallet/balance", {"miner_id": wallet_id})
        for key in ("balance", "amount_rtc"):
            if key in data:
                return float(data[key])
        raise ValueError(f"Unexpected balance response keys: {sorted(data)}")

    def list_bounties(self, limit: int = 10) -> list[dict[str, Any]]:
        # Public node deployments have used both paths; fail over without hiding errors.
        last_error: Exception | None = None
        for path in ("/api/bounties", "/bounties"):
            try:
                data = self._get(path, {"limit": limit})
                if isinstance(data, list):
                    return data[:limit]
                for key in ("bounties", "items", "results"):
                    if isinstance(data, dict) and isinstance(data.get(key), list):
                        return data[key][:limit]
                raise ValueError(f"Unexpected bounty response from {path}")
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
        raise RuntimeError("No supported public bounty endpoint responded") from last_error

    def get_node_health(self) -> dict[str, Any]:
        data = self._get("/health")
        if not isinstance(data, dict):
            raise ValueError("Unexpected health response")
        return data

    def get_current_epoch(self) -> dict[str, Any]:
        last_error: Exception | None = None
        for path in ("/api/epoch", "/epoch/current", "/api/epoch/current"):
            try:
                data = self._get(path)
                if isinstance(data, dict):
                    return data
                raise ValueError(f"Unexpected epoch response from {path}")
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
        raise RuntimeError("No supported public epoch endpoint responded") from last_error

    def _run(self, action: str, wallet_id: str | None = None, limit: int = 10) -> Any:
        if action == "check_balance":
            return self.check_balance(wallet_id or "")
        if action == "list_bounties":
            return self.list_bounties(limit)
        if action == "get_node_health":
            return self.get_node_health()
        if action == "get_current_epoch":
            return self.get_current_epoch()
        raise ValueError(f"Unsupported action: {action}")
