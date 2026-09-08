import json
from pathlib import Path

import pytest

from rtc_watchdog import assess_snapshot, build_beacon_envelope, run_once
from beacon_skill.identity import IdentityManager
from beacon_skill.protocol import EnvelopeKind


def snapshot(*transactions, balance=671.0):
    return {
        "balance": {"amount_rtc": balance, "miner_id": "RTCtest"},
        "history": {"ok": True, "transactions": list(transactions)},
    }


def pending(amount, timestamp, tx_hash="abc"):
    return {"amount": amount, "timestamp": timestamp, "tx_hash": tx_hash, "status": "pending"}


def settled(amount, timestamp, tx_hash="done"):
    return {"amount": amount, "timestamp": timestamp, "tx_hash": tx_hash, "status": "confirmed"}


def test_pending_inside_window_emits_heartbeat():
    now = 2_000_000
    state = assess_snapshot(snapshot(pending(10, now - 120), pending(2, now - 60, "def")), now=now)
    assert state.level == "heartbeat"
    assert state.pending_rtc == 12
    assert state.pending_count == 2
    assert state.stale_count == 0
    assert state.oldest_pending_age_seconds == 120

    envelope = build_beacon_envelope(state, IdentityManager())
    assert envelope.kind == EnvelopeKind.HEARTBEAT
    assert envelope.signature
    assert envelope.metadata["pending_rtc"] == 12


def test_stale_pending_emits_signed_mayday():
    now = 2_000_000
    state = assess_snapshot(snapshot(pending(18, now - 86401)), now=now)
    assert state.level == "mayday"
    assert state.stale_count == 1
    assert "exceeded" in state.reason

    envelope = build_beacon_envelope(state, IdentityManager())
    assert envelope.kind == EnvelopeKind.MAYDAY
    assert envelope.signature
    assert envelope.metadata["urgency"] == "high"
    assert envelope.metadata["requested_help"] == "maintainer settlement review"


def test_settled_rows_are_not_pending():
    now = 2_000_000
    state = assess_snapshot(snapshot(settled(50, now - 999999)), now=now)
    assert state.level == "heartbeat"
    assert state.pending_count == 0
    assert state.pending_rtc == 0
    assert state.oldest_pending_age_seconds is None


@pytest.mark.parametrize(
    "bad",
    [
        {},
        {"balance": {"amount_rtc": -1}, "history": {"ok": True, "transactions": []}},
        {"balance": {"amount_rtc": True}, "history": {"ok": True, "transactions": []}},
        {"balance": {"amount_rtc": 1}, "history": {"ok": False, "transactions": []}},
        {"balance": {"amount_rtc": 1}, "history": {"ok": True, "transactions": "oops"}},
    ],
)
def test_invalid_snapshot_fails_closed(bad):
    with pytest.raises(ValueError):
        assess_snapshot(bad, now=2_000_000)


def test_invalid_pending_row_fails_closed():
    with pytest.raises(ValueError):
        assess_snapshot(snapshot(pending(True, 10)), now=20)
    with pytest.raises(ValueError):
        assess_snapshot(snapshot(pending(1, True)), now=20)
    with pytest.raises(ValueError):
        assess_snapshot(snapshot(pending(1, 10, "")), now=20)


def test_run_once_serializes_signed_beacon(tmp_path: Path):
    path = tmp_path / "wallet_snapshot.json"
    path.write_text(json.dumps(snapshot(pending(1, 1_999_990))), encoding="utf-8")
    result = run_once(path, now=2_000_000)
    assert result["assessment"]["level"] == "heartbeat"
    assert result["signature_present"] is True
    assert result["beacon"]["kind"] == "heartbeat"
    assert result["beacon"]["metadata"]["component"] == "rtc-settlement-watchdog"
