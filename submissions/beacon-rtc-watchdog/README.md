# Beacon RTC Settlement Watchdog

A concrete Beacon integration for rustchain-bounties #158. Instead of another generic heartbeat demo, this agent turns RustChain payout state into Beacon coordination signals.

## What it does

1. Reads an authoritative RustChain wallet snapshot.
2. Keeps `received` and `pending` RTC separate.
3. Emits a cryptographically signed Beacon `HEARTBEAT` while settlement is healthy.
4. Emits a cryptographically signed Beacon `MAYDAY` only when a pending transfer exceeds the configured settlement threshold.
5. Fails closed on malformed wallet/history data rather than fabricating a healthy state.

The program never transfers funds or mutates a production RustChain endpoint.

## Beacon integration

The implementation uses the current `beacon-skill` primitives directly:

- `IdentityManager` generates/loads the Beacon Ed25519 identity.
- `BeaconEnvelope` carries watchdog state.
- `EnvelopeKind.HEARTBEAT` represents healthy operation.
- `EnvelopeKind.MAYDAY` represents settlement that needs maintainer attention.
- `envelope.sign(identity.keypair)` signs each emitted state.

This makes Beacon useful as an operational agent protocol rather than merely printing a canned hello message.

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
  "signature_present": true
}
```

After the configured threshold, still-pending transfers produce a `mayday` envelope with `urgency=high` and `requested_help=maintainer settlement review`. Age never promotes RTC to received; only the input wallet snapshot can do that.

## Test

```bash
pytest -q
```

Tests cover:
- healthy pending state → signed heartbeat
- stale pending state → signed mayday
- settled history excluded from pending totals
- malformed history/balance/pending rows fail closed
- serialized signed envelope output

## Why this is distinct

The #158 thread already contains generic Beacon heartbeat/discovery/mayday/contract demonstrations. This submission instead integrates Beacon into a real RTC operations workflow: settlement-state monitoring and escalation, with deterministic tests and strict accounting semantics.

RTC wallet: `RTCc5449fe1b93385961152720c864c0f073dae5855`
