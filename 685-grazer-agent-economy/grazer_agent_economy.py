#!/usr/bin/env python3
"""Read-only Grazer integration for the RustChain RIP-302 Agent Economy.

This module intentionally exposes only public GET routes. It never posts jobs,
claims work, submits deliveries, releases escrow, disputes work, or moves RTC.

Designed to mirror the small platform-specific clients used by grazer-skill
(e.g. ``BoTTubeGrazer``) while normalizing RIP-302 jobs into Grazer-friendly
content dictionaries.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlsplit

import requests

DEFAULT_NODE = "https://50.28.86.131"
VALID_STATUSES = {
    "open",
    "claimed",
    "delivered",
    "completed",
    "disputed",
    "expired",
    "cancelled",
}
VALID_CATEGORIES = {
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


class AgentEconomyGrazer:
    """Browse the RustChain Agent Economy using Grazer-style discovery methods.

    The integration is deliberately read-only. Every network call goes through
    ``Session.get`` to one of the RIP-302 public discovery endpoints:

    * ``GET /agent/jobs``
    * ``GET /agent/jobs/<job_id>``
    * ``GET /agent/reputation/<wallet_id>``
    * ``GET /agent/stats``

    A custom ``session`` can be injected for tests or for an operator-managed
    HTTP adapter.
    """

    platform = "rustchain-agent-economy"

    def __init__(
        self,
        base_url: str = DEFAULT_NODE,
        timeout: int = 15,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = self._validate_base_url(base_url)
        self.timeout = max(1, int(timeout))
        self.session = session or requests.Session()
        headers = getattr(self.session, "headers", None)
        if headers is not None and hasattr(headers, "update"):
            headers.update({"User-Agent": "Grazer-Agent-Economy/1.0 (read-only)"})

    @staticmethod
    def _validate_base_url(value: str) -> str:
        candidate = str(value or "").strip().rstrip("/")
        parts = urlsplit(candidate)
        if parts.scheme not in {"http", "https"} or not parts.netloc:
            raise ValueError("base_url must be an absolute http(s) URL")
        return candidate

    @staticmethod
    def _clean_limit(limit: int) -> int:
        return min(100, max(1, int(limit)))

    @staticmethod
    def _clean_offset(offset: int) -> int:
        return max(0, int(offset))

    @staticmethod
    def _clean_min_reward(min_reward: float) -> float:
        value = float(min_reward)
        if value < 0:
            raise ValueError("min_reward must be non-negative")
        return value

    def _get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}{path}", params=params, timeout=self.timeout
        )
        response.raise_for_status()
        payload = response.json() if callable(response.json) else response.json
        if not isinstance(payload, dict):
            raise ValueError("RustChain Agent Economy returned non-object JSON")
        return payload

    def discover(
        self,
        *,
        status: str = "open",
        category: Optional[str] = None,
        min_reward: float = 0,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Browse jobs ordered by reward then recency, matching RIP-302 behavior."""
        status = str(status or "open").strip().lower()
        if status not in VALID_STATUSES:
            raise ValueError(f"unsupported status: {status}")

        params: Dict[str, Any] = {
            "status": status,
            "min_reward": self._clean_min_reward(min_reward),
            "limit": self._clean_limit(limit),
            "offset": self._clean_offset(offset),
        }
        if category:
            category = str(category).strip().lower()
            if category not in VALID_CATEGORIES:
                raise ValueError(f"unsupported category: {category}")
            params["category"] = category

        payload = self._get_json("/agent/jobs", params=params)
        jobs = payload.get("jobs", [])
        if not isinstance(jobs, list):
            return []
        return [self._normalize_job(job) for job in jobs if isinstance(job, dict)]

    def job(self, job_id: str) -> Dict[str, Any]:
        """Return one job with its activity log and ratings, if present."""
        job_id = str(job_id or "").strip()
        if not job_id:
            raise ValueError("job_id is required")
        payload = self._get_json(f"/agent/jobs/{job_id}")
        job = payload.get("job", {})
        return self._normalize_job(job) if isinstance(job, dict) else {}

    def reputation(self, wallet_id: str) -> Dict[str, Any]:
        """Return the public reputation record for a wallet."""
        wallet_id = str(wallet_id or "").strip()
        if not wallet_id:
            raise ValueError("wallet_id is required")
        payload = self._get_json(f"/agent/reputation/{wallet_id}")
        rep = payload.get("reputation")
        if rep is None:
            return {
                "wallet_id": payload.get("wallet_id", wallet_id),
                "reputation": None,
                "message": payload.get("message", "No reputation history"),
            }
        if not isinstance(rep, dict):
            return {}
        normalized = dict(rep)
        normalized.setdefault("wallet_id", payload.get("wallet_id", wallet_id))
        return normalized

    def stats(self) -> Dict[str, Any]:
        """Return public marketplace summary statistics."""
        payload = self._get_json("/agent/stats")
        stats = payload.get("stats", {})
        return dict(stats) if isinstance(stats, dict) else {}

    def search(
        self,
        query: str,
        *,
        status: str = "open",
        category: Optional[str] = None,
        min_reward: float = 0,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search the highest-value matching jobs using public browse data.

        RIP-302 currently has no server-side free-text search route. This method
        fetches up to 100 jobs from the selected status/category and performs a
        deterministic local match over title, description, tags, and wallets.
        """
        needle = str(query or "").strip().casefold()
        if not needle:
            return self.discover(
                status=status,
                category=category,
                min_reward=min_reward,
                limit=limit,
            )

        jobs = self.discover(
            status=status,
            category=category,
            min_reward=min_reward,
            limit=100,
        )
        matches = []
        for job in jobs:
            haystack = " ".join(
                str(value)
                for value in (
                    job.get("title", ""),
                    job.get("description", ""),
                    " ".join(map(str, job.get("tags", []))),
                    job.get("poster_wallet", ""),
                    job.get("worker_wallet", ""),
                )
            ).casefold()
            if needle in haystack:
                matches.append(job)
                if len(matches) >= self._clean_limit(limit):
                    break
        return matches

    def high_value(
        self,
        *,
        min_reward: float = 25,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Convenience discovery lane for open jobs above a reward threshold."""
        return self.discover(
            status="open",
            category=category,
            min_reward=min_reward,
            limit=limit,
        )

    def _normalize_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Map a RIP-302 job to fields Grazer already knows how to consume."""
        job_id = str(job.get("job_id", job.get("id", "")) or "")
        tags = job.get("tags", [])
        if isinstance(tags, str):
            try:
                decoded = json.loads(tags)
                tags = decoded if isinstance(decoded, list) else [tags]
            except (TypeError, ValueError, json.JSONDecodeError):
                tags = [tags] if tags else []
        elif not isinstance(tags, list):
            tags = []

        api_url = f"{self.base_url}/agent/jobs/{job_id}" if job_id else ""
        normalized: Dict[str, Any] = {
            "id": job_id,
            "job_id": job_id,
            "platform": self.platform,
            "title": job.get("title", ""),
            "description": job.get("description", ""),
            "content": job.get("description", ""),
            "category": job.get("category", "other"),
            "reward_rtc": job.get("reward_rtc", 0),
            "status": job.get("status", ""),
            "poster_wallet": job.get("poster_wallet", ""),
            "worker_wallet": job.get("worker_wallet", ""),
            "author": job.get("poster_wallet", ""),
            "creator": job.get("poster_wallet", ""),
            "created_at": job.get("created_at", ""),
            "expires_at": job.get("expires_at", ""),
            "tags": tags,
            "url": api_url,
            "canonical_url": api_url,
        }

        for key in (
            "claimed_at",
            "delivered_at",
            "completed_at",
            "deliverable_url",
            "result_summary",
            "rejection_reason",
            "activity_log",
            "ratings",
        ):
            if key in job:
                normalized[key] = job.get(key)
        return normalized


def _print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only Grazer browser for the RustChain RIP-302 Agent Economy"
    )
    parser.add_argument("--node", default=DEFAULT_NODE, help="RustChain node base URL")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout seconds")
    sub = parser.add_subparsers(dest="command", required=True)

    jobs = sub.add_parser("jobs", help="Browse jobs")
    jobs.add_argument("--status", default="open", choices=sorted(VALID_STATUSES))
    jobs.add_argument("--category", choices=sorted(VALID_CATEGORIES))
    jobs.add_argument("--min-reward", type=float, default=0)
    jobs.add_argument("--limit", type=int, default=20)
    jobs.add_argument("--offset", type=int, default=0)

    hv = sub.add_parser("high-value", help="Browse high-value open jobs")
    hv.add_argument("--min-reward", type=float, default=25)
    hv.add_argument("--category", choices=sorted(VALID_CATEGORIES))
    hv.add_argument("--limit", type=int, default=20)

    one = sub.add_parser("job", help="Show one job")
    one.add_argument("job_id")

    rep = sub.add_parser("reputation", help="Show public wallet reputation")
    rep.add_argument("wallet_id")

    sub.add_parser("stats", help="Show marketplace stats")

    search = sub.add_parser("search", help="Search public browse results locally")
    search.add_argument("query")
    search.add_argument("--status", default="open", choices=sorted(VALID_STATUSES))
    search.add_argument("--category", choices=sorted(VALID_CATEGORIES))
    search.add_argument("--min-reward", type=float, default=0)
    search.add_argument("--limit", type=int, default=20)

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    client = AgentEconomyGrazer(args.node, timeout=args.timeout)

    if args.command == "jobs":
        result = client.discover(
            status=args.status,
            category=args.category,
            min_reward=args.min_reward,
            limit=args.limit,
            offset=args.offset,
        )
    elif args.command == "high-value":
        result = client.high_value(
            min_reward=args.min_reward,
            category=args.category,
            limit=args.limit,
        )
    elif args.command == "job":
        result = client.job(args.job_id)
    elif args.command == "reputation":
        result = client.reputation(args.wallet_id)
    elif args.command == "stats":
        result = client.stats()
    elif args.command == "search":
        result = client.search(
            args.query,
            status=args.status,
            category=args.category,
            min_reward=args.min_reward,
            limit=args.limit,
        )
    else:
        raise AssertionError(args.command)

    _print_json(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
