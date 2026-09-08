# Beacon RTC Settlement Watchdog

A concrete Beacon integration for rustchain-bounties #158. Instead of another generic heartbeat demo, this agent turns RustChain payout state into Beacon coordination signals.

## What it does

1. Reads an authoritative RustChain wallet snapshot.
2. Keeps `received` and `pending` RTC separate.
3. Emits a cryptographically signed Beacon `heartbeat` while settlement is healthy.
4. Emits a cryptographically signed Beacon `mayday` only when a pending transfer exceeds the configured settlement threshold.
5. Fails closed on malformed wallet/history data rather than fabricating a healthy state.

The program never transfers funds or mutates a production RustChain endpoint.

## Beacon integration

The implementation uses the current `beacon-skill` API directly:

- `AgentIdentity.generate()` creates a Beacon Ed25519 identity.
- `HeartbeatManager.build_heartbeat()` creates the normal-operation protocol payload.
- `MaydayManager.build_mayday()` creates the escalation payload with `urgency=imminent`.
- `AgentIdentity.sign_hex()` signs a canonical JSON representation of each emitted payload.
- `AgentIdentity.verify()` verifies the signature in tests and in the returned result.

Settlement-specific metrics are carried under `health` on heartbeat payloads and under `settlement` on mayday payloads. This makes Beacon useful as an operational agent protocol rather than merely printing a canned hello message.

## Run

```bash
python -m pip install beacon-skill pytest
python rtc_watchdog.py ../../ops/wallet_snapshot.json
```

Example healthy output contains:

```json
{
  "assessment": {
    "level": "heartbeat",
    "received_rtc": 671.0,
    "pending_rtc": 18.0,
    "stale_count": 0
  },
  "signature_valid": true,
  "beacon": {
    "kind": "heartbeat"
  }
}
```

After the configured threshold, still-pending transfers produce a `mayday` payload with `urgency=imminent` and `requested_help=maintainer settlement review`. Age never promotes RTC to received; only the input wallet snapshot can do that.

## Test

```bash
pytest -q
```

Tests cover:
- healthy pending state → signed heartbeat
- stale pending state → signed mayday
- Ed25519 signature verification
- settled history excluded from pending totals
- malformed history/balance/pending rows fail closed
- serialized signed payload output

## Why this is distinct

The #158 thread already contains generic Beacon heartbeat/discovery/mayday/contract demonstrations. This submission instead integrates Beacon into a real RTC operations workflow: settlement-state monitoring and escalation, with deterministic tests and strict accounting semantics.

RTC wallet: `RTCc5449fe1b93385961152720c864c0f073dae5855`
