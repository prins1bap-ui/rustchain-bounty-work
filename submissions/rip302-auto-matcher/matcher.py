#!/usr/bin/env python3
"""Explainable worker auto-matching for RustChain RIP-302 bounty #683."""

from __future__ import annotations

import argparse
import json
import math
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any, Iterable

DEFAULT_BASE_URL = "https://rustchain.org"


@dataclass(frozen=True)
class Candidate:
    wallet: str
    trust_score: float = 0.0
    avg_rating: float = 0.0
    completed_jobs: int = 0
    total_rtc_earned: float = 0.0
    active_jobs: int = 0
    categories: tuple[str, ...] = ()


@dataclass(frozen=True)
class RankedCandidate:
    wallet: str
    score: float
    reasons: tuple[str, ...]
    components: dict[str, float]


def _bounded(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def score_candidate(job: dict[str, Any], candidate: Candidate) -> RankedCandidate:
    """Score one worker on a 0-100 scale using reputation and capacity.

    Weighting deliberately favors established trust while retaining room for
    newer workers. Every component is returned so the recommendation can be
    audited instead of becoming an opaque ranking oracle.
    """
    trust = _bounded(candidate.trust_score, 0, 100)
    rating = _bounded(candidate.avg_rating, 0, 5) / 5 * 100
    experience = min(100.0, math.log1p(max(0, candidate.completed_jobs)) / math.log(21) * 100)
    earned = min(100.0, math.log1p(max(0.0, candidate.total_rtc_earned)) / math.log(501) * 100)
    capacity = max(0.0, 100 - max(0, candidate.active_jobs) * 20)

    category = str(job.get("category") or "").strip().lower()
    candidate_categories = {c.strip().lower() for c in candidate.categories if c.strip()}
    category_fit = 100.0 if category and category in candidate_categories else (50.0 if not candidate_categories else 25.0)

    components = {
        "trust": round(trust, 2),
        "rating": round(rating, 2),
        "experience": round(experience, 2),
        "earnings_history": round(earned, 2),
        "capacity": round(capacity, 2),
        "category_fit": round(category_fit, 2),
    }
    score = (
        0.35 * trust
        + 0.20 * rating
        + 0.15 * experience
        + 0.05 * earned
        + 0.10 * capacity
        + 0.15 * category_fit
    )

    reasons = [f"trust {trust:.0f}/100", f"rating {candidate.avg_rating:.1f}/5", f"completed {candidate.completed_jobs} jobs"]
    if category and category in candidate_categories:
        reasons.append(f"verified category fit: {category}")
    elif candidate_categories:
        reasons.append(f"no recorded {category or 'requested'} category fit")
    if candidate.active_jobs:
        reasons.append(f"capacity penalty: {candidate.active_jobs} active job(s)")
    else:
        reasons.append("no active-job capacity penalty")

    return RankedCandidate(candidate.wallet, round(score, 2), tuple(reasons), components)


def rank_candidates(job: dict[str, Any], candidates: Iterable[Candidate], limit: int = 5) -> list[RankedCandidate]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    unique: dict[str, Candidate] = {}
    for candidate in candidates:
        wallet = candidate.wallet.strip()
        if not wallet:
            raise ValueError("candidate wallet is required")
        unique[wallet] = candidate
    ranked = [score_candidate(job, c) for c in unique.values()]
    ranked.sort(key=lambda x: (-x.score, x.wallet.lower()))
    return ranked[:limit]


def fetch_json(url: str, timeout: float = 10.0) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "rustchain-rip302-auto-matcher/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = json.load(response)
    if not isinstance(data, dict):
        raise ValueError("API response must be a JSON object")
    return data


def candidate_from_reputation(wallet: str, payload: dict[str, Any], *, active_jobs: int = 0, categories: Iterable[str] = ()) -> Candidate:
    """Normalize the evolving reputation API without inventing missing values."""
    return Candidate(
        wallet=wallet,
        trust_score=float(payload.get("trust_score") or 0),
        avg_rating=float(payload.get("avg_rating") or 0),
        completed_jobs=int(payload.get("completed_jobs") or 0),
        total_rtc_earned=float(payload.get("total_rtc_earned") or 0),
        active_jobs=max(0, int(active_jobs)),
        categories=tuple(categories),
    )


def match_live(job: dict[str, Any], wallets: Iterable[str], *, base_url: str = DEFAULT_BASE_URL, limit: int = 5) -> list[RankedCandidate]:
    base = base_url.rstrip("/")
    candidates = []
    for wallet in wallets:
        wallet = wallet.strip()
        if not wallet:
            continue
        encoded = urllib.parse.quote(wallet, safe="")
        payload = fetch_json(f"{base}/agent/reputation/{encoded}")
        candidates.append(candidate_from_reputation(wallet, payload))
    return rank_candidates(job, candidates, limit=limit)


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank RIP-302 workers for a job using reputation evidence")
    parser.add_argument("--job", required=True, help="JSON job object")
    parser.add_argument("--wallet", action="append", required=True, dest="wallets")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    job = json.loads(args.job)
    if not isinstance(job, dict):
        raise ValueError("--job must decode to a JSON object")
    ranked = match_live(job, args.wallets, base_url=args.base_url, limit=args.limit)
    print(json.dumps([asdict(item) for item in ranked], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
