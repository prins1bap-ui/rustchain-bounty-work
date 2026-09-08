#!/usr/bin/env python3
"""Beacon-integrated RTC settlement watchdog for bounty #158.

Reads a RustChain wallet snapshot, classifies settlement health, and emits a
signed Beacon heartbeat while healthy or a signed Beacon mayday when pending
transfers become stale. Age never promotes RTC to received.

No funds are moved and no production endpoint is mutated by this program.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from beacon_skill.heartbeat import HeartbeatManager
from beacon_skill.identity import AgentIdentity
from beacon_skill.mayday import MaydayManager, URGENCY_IMMINENT


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
    """Classify wallet state without guessing that age implies settlement."""
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


def _settlement_metadata(assessment: Assessment) -> dict[str, Any]:
    return {
        "component": "rtc-settlement-watchdog",
        "received_rtc": assessment.received_rtc,
        "pending_rtc": assessment.pending_rtc,
        "pending_count": assessment.pending_count,
        "stale_count": assessment.stale_count,
        "newest_pending_age_seconds": assessment.newest_pending_age_seconds,
        "oldest_pending_age_seconds": assessment.oldest_pending_age_seconds,
        "reason": assessment.reason,
    }


def _canonical_unsigned(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        {k: v for k, v in payload.items() if k != "sig"},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sign_payload(payload: dict[str, Any], identity: AgentIdentity) -> dict[str, Any]:
    """Attach the current Beacon identity public key and Ed25519 signature."""
    signed = dict(payload)
    signed["pubkey"] = identity.public_key_hex
    signed["sig"] = identity.sign_hex(_canonical_unsigned(signed))
    return signed


def verify_payload_signature(payload: dict[str, Any]) -> bool:
    pubkey = payload.get("pubkey")
    signature = payload.get("sig")
    if not isinstance(pubkey, str) or not isinstance(signature, str):
        return False
    return AgentIdentity.verify(pubkey, signature, _canonical_unsigned(payload))


def build_beacon_payload(
    assessment: Assessment, identity: AgentIdentity, *, data_dir: Path
) -> dict[str, Any]:
    """Build a current Beacon heartbeat/mayday payload and sign it."""
    metadata = _settlement_metadata(assessment)
    if assessment.level == "heartbeat":
        mgr = HeartbeatManager(
            data_dir=data_dir,
            config={"beacon": {"agent_name": "rtc-settlement-watchdog"}},
        )
        payload = mgr.build_heartbeat(
            identity,
            status="alive",
            health=metadata,
            config={"beacon": {"agent_name": "rtc-settlement-watchdog"}},
        )
    elif assessment.level == "mayday":
        mgr = MaydayManager(data_dir=data_dir)
        payload = mgr.build_mayday(
            identity,
            urgency=URGENCY_IMMINENT,
            reason=assessment.reason,
            config={"beacon": {"agent_name": "rtc-settlement-watchdog"}},
        )
        payload["settlement"] = {
            **metadata,
            "requested_help": "maintainer settlement review",
        }
    else:
        raise ValueError(f"unsupported assessment level: {assessment.level}")
    return sign_payload(payload, identity)


def run_once(
    snapshot_path: Path,
    *,
    now: int | None = None,
    stale_after_seconds: int = 86400,
    data_dir: Path | None = None,
) -> dict[str, Any]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot root must be an object")
    assessment = assess_snapshot(snapshot, now=now, stale_after_seconds=stale_after_seconds)
    identity = AgentIdentity.generate()

    if data_dir is not None:
        payload = build_beacon_payload(assessment, identity, data_dir=data_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="beacon-rtc-watchdog-") as tmp:
            payload = build_beacon_payload(assessment, identity, data_dir=Path(tmp))

    return {
        "assessment": assessment.__dict__,
        "beacon": payload,
        "signature_valid": verify_payload_signature(payload),
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
