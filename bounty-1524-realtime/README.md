# RustChain bounty #1524: Beacon Atlas real-time WebSocket feed

Claimant: `@prins1bap-ui`  
RTC wallet: `RTCc5449fe1b93385961152720c864c0f073dae5855`  
Track: **Real-time updates — 25 RTC**

## What this delivers

A read-only `/beacon/ws` WebSocket feed for new Beacon agents, relay heartbeats, contract creation/state changes, and removals. The implementation is split into a testable SQLite delta engine (`node/beacon_realtime.py`) and a browser client (`site/beacon/realtime.js`) with secure `wss://` selection, reconnect backoff, schema checks, event ordering, and browser `beacon:realtime` events.

The backend intentionally redacts data that the current source treats as sensitive. The public stream does **not** expose agent public keys, payment addresses, contract terms, amounts, or currency. It sends only the fields required to identify Atlas objects and react to their state changes.

## Upstream integration

The included `rustchain-1524-realtime.patch` makes four focused changes:

1. add `simple-websocket>=1.1.0` to `requirements.txt`;
2. add `node/beacon_realtime.py`;
3. register a read-only `GET /beacon/ws` WebSocket route in `node/beacon_api.py`;
4. load `site/beacon/realtime.js` from the Atlas boot script and expose connection/event state through the existing HUD/console plus a `beacon:realtime` browser event.

No payment, contract-creation, wallet, signing, or fund-control path is added or changed.

## Event protocol

Every frame is JSON with protocol version `v: 1`, a monotonically increasing connection-local `seq`, `type`, server timestamp `ts`, and `data`.

Supported event types:

- `hello`
- `agent.new`
- `agent.updated`
- `agent.heartbeat`
- `agent.removed`
- `contract.new`
- `contract.updated`
- `contract.removed`

A heartbeat is emitted when an existing relay agent's `updated_at` changes without a public profile/status change. This matches the current join/rejoin behavior, where `relay_agents.updated_at` is refreshed.

## Validation

Executed locally against an isolated SQLite database matching the current `relay_agents` and `beacon_contracts` schemas:

```text
python -m unittest discover -s tests -p 'test_beacon_realtime.py' -v
5 tests passed

node tests/test_realtime_parser.mjs
realtime.js static contract checks passed
```

The tests cover:

- new-agent and new-contract events;
- heartbeat detection separately from profile updates;
- contract/profile updates;
- removal tombstones;
- deterministic monotonic sequence ordering;
- explicit proof that sensitive pubkey/payment/contract-term/amount fields are absent from event payloads;
- client event schema, ordering guard, and secure WebSocket URL handling.

## Why this is distinct

Before implementation I checked the open #1524 thread and the upstream RustChain PR/code search for the advertised real-time/WebSocket track. I found no submitted PR implementing this track, while the repository's own #1524 implementation notes still list WebSocket live updates as a future enhancement.

## Files

- `node/beacon_realtime.py` — SQLite snapshot/delta engine + WebSocket streamer
- `site/beacon/realtime.js` — reconnecting browser WebSocket client
- `tests/test_beacon_realtime.py` — deterministic backend tests
- `tests/test_realtime_parser.mjs` — browser-client contract checks
- `rustchain-1524-realtime.patch` — maintainer-ready upstream integration patch
