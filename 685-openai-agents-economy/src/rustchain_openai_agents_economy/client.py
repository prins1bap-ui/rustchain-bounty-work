"""Read-only async client for the RIP-302 Agent Economy marketplace."""

from __future__ import annotations

import math
import re
from typing import Any

import httpx

_SEGMENT = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
_STATUSES = {"open", "claimed", "delivered", "completed", "disputed", "cancelled", "expired"}
_CATEGORIES = {
    "research",
    "code",
    "video",
    "audio",
    "writing",
    "translation",
    "data",
    "design",
    "testing",
    "other",
}


class AgentEconomyError(RuntimeError):
    """Raised when the marketplace returns an unsuccessful or malformed response."""


class AgentEconomyReadClient:
    """GET-only client for marketplace discovery, details, reputation, and stats."""

    def __init__(
        self,
        base_url: str = "https://50.28.86.131",
        *,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        base_url = base_url.strip().rstrip("/")
        if not base_url.startswith(("https://", "http://")):
            raise ValueError("base_url must be http(s)")
        self._http = httpx.AsyncClient(base_url=base_url, timeout=timeout, transport=transport)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AgentEconomyReadClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    @staticmethod
    def _segment(value: str, label: str) -> str:
        value = value.strip()
        if not _SEGMENT.fullmatch(value):
            raise ValueError(f"invalid {label}")
        return value

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = await self._http.get(path, params=params)
        if not response.is_success:
            body = response.text[:500]
            raise AgentEconomyError(f"GET {path} returned {response.status_code}: {body}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise AgentEconomyError(f"GET {path} returned non-JSON data") from exc
        if not isinstance(payload, dict):
            raise AgentEconomyError(f"GET {path} returned a non-object JSON payload")
        return payload

    async def browse_jobs(
        self,
        *,
        status: str | None = "open",
        category: str | None = None,
        min_reward: float | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer from 1 to 100")
        if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
            raise ValueError("offset must be a non-negative integer")
        if status is not None and status not in _STATUSES:
            raise ValueError("unsupported status")
        if category is not None and category not in _CATEGORIES:
            raise ValueError("unsupported category")
        if min_reward is not None:
            if isinstance(min_reward, bool) or not isinstance(min_reward, (int, float)):
                raise ValueError("min_reward must be numeric")
            if not math.isfinite(float(min_reward)) or min_reward < 0:
                raise ValueError("min_reward must be finite and non-negative")

        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status is not None:
            params["status"] = status
        if category is not None:
            params["category"] = category
        if min_reward is not None:
            params["min_reward"] = min_reward
        return await self._get("/agent/jobs", params=params)

    async def get_job(self, job_id: str) -> dict[str, Any]:
        job_id = self._segment(job_id, "job_id")
        return await self._get(f"/agent/jobs/{job_id}")

    async def get_reputation(self, wallet: str) -> dict[str, Any]:
        wallet = self._segment(wallet, "wallet")
        return await self._get(f"/agent/reputation/{wallet}")

    async def get_stats(self) -> dict[str, Any]:
        return await self._get("/agent/stats")
