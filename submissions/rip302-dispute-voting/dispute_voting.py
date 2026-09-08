#!/usr/bin/env python3
"""Reputation-weighted dispute settlement engine for RIP-302 bounty #683.

This module does not execute payouts. It produces a deterministic settlement
recommendation from eligible voter evidence so a human or node-side adapter can
apply the result through the existing Agent Economy controls.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Iterable


class Choice(str, Enum):
    WORKER = "worker"
    POSTER = "poster"
    ABSTAIN = "abstain"


@dataclass(frozen=True)
class Voter:
    wallet: str
    trust_score: float
    completed_jobs: int = 0
    disputes_participated: int = 0


@dataclass(frozen=True)
class Vote:
    voter_wallet: str
    choice: Choice
    reason: str = ""


@dataclass(frozen=True)
class Settlement:
    dispute_id: str
    outcome: str
    quorum_met: bool
    worker_weight: float
    poster_weight: float
    abstain_weight: float
    eligible_voters: int
    votes_counted: int
    threshold: float
    rationale: tuple[str, ...]
    evidence_hash: str


def voting_weight(voter: Voter, *, min_trust: float = 50.0) -> float:
    """Return bounded voting weight for an eligible reputation holder.

    Trust supplies most of the weight; proven marketplace participation adds a
    small logarithmic bonus. This prevents a single veteran from having
    unlimited authority while still rewarding demonstrated history.
    """
    if not voter.wallet.strip():
        raise ValueError("voter wallet is required")
    trust = max(0.0, min(100.0, float(voter.trust_score)))
    if trust < min_trust:
        return 0.0
    experience_bonus = min(20.0, max(0, voter.completed_jobs) ** 0.5 * 2.0)
    civic_bonus = min(5.0, max(0, voter.disputes_participated) * 0.25)
    return round(1.0 + trust / 100.0 * 4.0 + experience_bonus / 20.0 + civic_bonus / 5.0, 6)


def _evidence_hash(dispute_id: str, voters: dict[str, Voter], votes: Iterable[Vote]) -> str:
    payload = {
        "dispute_id": dispute_id,
        "voters": [asdict(voters[k]) for k in sorted(voters)],
        "votes": [
            {"voter_wallet": v.voter_wallet, "choice": v.choice.value, "reason": v.reason}
            for v in sorted(votes, key=lambda x: (x.voter_wallet.lower(), x.choice.value, x.reason))
        ],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def settle_dispute(
    dispute_id: str,
    voters: Iterable[Voter],
    votes: Iterable[Vote],
    *,
    min_trust: float = 50.0,
    min_voters: int = 3,
    decision_threshold: float = 0.60,
) -> Settlement:
    """Produce a deterministic worker/poster/no-decision recommendation.

    Rules:
    - one effective vote per wallet; duplicate vote records fail closed
    - voters below min_trust have zero eligibility
    - quorum requires min_voters distinct eligible votes, including abstentions
    - winner must hold decision_threshold of non-abstaining weighted votes
    - a tie or insufficient threshold yields no_decision
    """
    if not dispute_id.strip():
        raise ValueError("dispute_id is required")
    if min_voters < 1:
        raise ValueError("min_voters must be positive")
    if not 0.5 < decision_threshold <= 1.0:
        raise ValueError("decision_threshold must be in (0.5, 1.0]")

    voter_map: dict[str, Voter] = {}
    for voter in voters:
        key = voter.wallet.strip()
        if not key:
            raise ValueError("voter wallet is required")
        if key in voter_map:
            raise ValueError(f"duplicate voter: {key}")
        voter_map[key] = voter

    vote_list = list(votes)
    seen_votes: set[str] = set()
    worker_weight = poster_weight = abstain_weight = 0.0
    counted = 0
    eligible_voters = sum(voting_weight(v, min_trust=min_trust) > 0 for v in voter_map.values())
    rationale: list[str] = []

    for vote in vote_list:
        wallet = vote.voter_wallet.strip()
        if wallet in seen_votes:
            raise ValueError(f"duplicate vote from {wallet}")
        seen_votes.add(wallet)
        voter = voter_map.get(wallet)
        if voter is None:
            rationale.append(f"ignored unknown voter {wallet}")
            continue
        weight = voting_weight(voter, min_trust=min_trust)
        if weight <= 0:
            rationale.append(f"ignored ineligible voter {wallet}")
            continue
        counted += 1
        if vote.choice is Choice.WORKER:
            worker_weight += weight
        elif vote.choice is Choice.POSTER:
            poster_weight += weight
        elif vote.choice is Choice.ABSTAIN:
            abstain_weight += weight
        else:
            raise ValueError(f"unsupported choice: {vote.choice}")

    worker_weight = round(worker_weight, 6)
    poster_weight = round(poster_weight, 6)
    abstain_weight = round(abstain_weight, 6)
    quorum_met = counted >= min_voters
    decisive_total = worker_weight + poster_weight

    outcome = "no_decision"
    if not quorum_met:
        rationale.append(f"quorum not met: {counted}/{min_voters} eligible votes")
    elif decisive_total <= 0:
        rationale.append("all eligible votes abstained")
    else:
        worker_share = worker_weight / decisive_total
        poster_share = poster_weight / decisive_total
        if worker_share >= decision_threshold and worker_weight > poster_weight:
            outcome = "worker"
            rationale.append(f"worker reached {worker_share:.1%} of decisive weight")
        elif poster_share >= decision_threshold and poster_weight > worker_weight:
            outcome = "poster"
            rationale.append(f"poster reached {poster_share:.1%} of decisive weight")
        else:
            rationale.append(
                f"neither side reached {decision_threshold:.0%}: worker {worker_share:.1%}, poster {poster_share:.1%}"
            )

    return Settlement(
        dispute_id=dispute_id,
        outcome=outcome,
        quorum_met=quorum_met,
        worker_weight=worker_weight,
        poster_weight=poster_weight,
        abstain_weight=abstain_weight,
        eligible_voters=eligible_voters,
        votes_counted=counted,
        threshold=decision_threshold,
        rationale=tuple(rationale),
        evidence_hash=_evidence_hash(dispute_id, voter_map, vote_list),
    )
