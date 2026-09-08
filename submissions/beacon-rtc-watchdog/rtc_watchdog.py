#!/usr/bin/env python3
"""Beacon-integrated RTC settlement watchdog for bounty #158.

The agent reads a RustChain wallet snapshot, classifies settlement health, and
emits a signed Beacon HEARTBEAT during normal operation or a signed MAYDAY when
pending transfers become stale or the snapshot is inconsistent.

No funds are moved and no production endpoint is mutated by this program.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from beacon_skill.identity import IdentityManager
from beacon_skill.protocol import BeaconEnvelope, EnvelopeKind


@dataclass(frozen=True)
class Transfer:
    amount: float
    timestamp: int
    tx_hash: str
    status: str


@dataclass(frozen=True)
class Assessment:
    level: str
    received_rtc: float
    pending_rtc: float
    pending_count: int
    stale_count: int
    newest_pending_age_seconds: int | None
    oldest_pending_age_seconds: int | None
    reason: str


def _transactions(snapshot: dict[str, Any]) -> Iterable[dict[str, Any]]:
    history = snapshot.get("history")
    if not isinstance(history, dict) or history.get("ok") is not True:
        raise ValueError("snapshot history must be an object with ok=true")
    rows = history.get("transactions")
    if not isinstance(rows, list):
        raise ValueError("snapshot history.transactions must be a list")
    return rows


def assess_snapshot(
    snapshot: dict[str, Any], *, now: int | None = None, stale_after_seconds: int = 24 * 3600
) -> Assessment:
    """Classify the wallet state without guessing that age implies settlement."""
    if stale_after_seconds <= 0:
        raise ValueError("stale_after_seconds must be positive")
    now = int(time.time()) if now is None else int(now)

    balance = snapshot.get("balance")
    if not isinstance(balance, dict):
        raise ValueError("snapshot balance must be an object")
    amount = balance.get("amount_rtc")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount < 0:
        raise ValueError("balance.amount_rtc must be a non-negative number")

    pending: list[Transfer] = []
    for row in _transactions(snapshot):
        if not isinstance(row, dict):
            raise ValueError("transaction rows must be objects")
        if row.get("status") != "pending":
            continue
        raw_amount = row.get("amount")
        ts = row.get("timestamp")
        tx_hash = row.get("tx_hash")
        if (
            isinstance(raw_amount, bool)
            or not isinstance(raw_amount, (int, float))
            or raw_amount < 0
            or isinstance(ts, bool)
            or not isinstance(ts, int)
            or ts <= 0
            or not isinstance(tx_hash, str)
            or not tx_hash.strip()
        ):
            raise ValueError("pending transaction contains invalid amount/timestamp/hash")
        pending.append(Transfer(float(raw_amount), ts, tx_hash, "pending"))

    ages = [max(0, now - tx.timestamp) for tx in pending]
    stale_count = sum(age >= stale_after_seconds for age in ages)
    pending_rtc = sum(tx.amount for tx in pending)

    if stale_count:
        level = "mayday"
        reason = f"{stale_count} pending transfer(s) exceeded the {stale_after_seconds}s settlement threshold"
    elif pending:
        level = "heartbeat"
        reason = "pending transfers remain inside the settlement threshold"
    else:
        level = "heartbeat"
        reason = "wallet has no pending transfers"

    return Assessment(
        level=level,
        received_rtc=float(amount),
        pending_rtc=round(pending_rtc, 8),
        pending_count=len(pending),
        stale_count=stale_count,
        newest_pending_age_seconds=min(ages) if ages else None,
        oldest_pending_age_seconds=max(ages) if ages else None,
        reason=reason,
    )


def build_beacon_envelope(assessment: Assessment, identity: IdentityManager) -> BeaconEnvelope:
    """Build and cryptographically sign the appropriate Beacon v2 envelope."""
    if assessment.level not in {"heartbeat", "mayday"}:
        raise ValueError(f"unsupported assessment level: {assessment.level}")

    kind = EnvelopeKind.MAYDAY if assessment.level == "mayday" else EnvelopeKind.HEARTBEAT
    metadata = {
        "component": "rtc-settlement-watchdog",
        "received_rtc": assessment.received_rtc,
        "pending_rtc": assessment.pending_rtc,
        "pending_count": assessment.pending_count,
        "stale_count": assessment.stale_count,
        "oldest_pending_age_seconds": assessment.oldest_pending_age_seconds,
        "reason": assessment.reason,
    }
    if assessment.level == "mayday":
        metadata.update({"urgency": "high", "requested_help": "maintainer settlement review"})

    envelope = BeaconEnvelope(
        kind=kind,
        text=assessment.reason,
        agent_id=identity.agent_id,
        metadata=metadata,
    )
    envelope.sign(identity.keypair)
    return envelope


def run_once(snapshot_path: Path, *, now: int | None = None, stale_after_seconds: int = 86400) -> dict[str, Any]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot root must be an object")
    assessment = assess_snapshot(snapshot, now=now, stale_after_seconds=stale_after_seconds)
    identity = IdentityManager()
    envelope = build_beacon_envelope(assessment, identity)
    return {
        "assessment": assessment.__dict__,
        "beacon": json.loads(envelope.to_json()),
        "signature_present": bool(envelope.signature),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit Beacon health state for an RTC wallet snapshot")
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--stale-after-seconds", type=int, default=86400)
    args = parser.parse_args()
    result = run_once(args.snapshot, stale_after_seconds=args.stale_after_seconds)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
