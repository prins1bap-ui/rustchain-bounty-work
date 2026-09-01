"""Beacon Atlas real-time event feed helpers.

This module is intentionally independent from Flask so the event-diffing core can
be tested without a web server. The Flask route in ``node/beacon_api.py`` passes
``request.environ`` to :func:`stream_beacon_events`.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Mapping, Optional


@dataclass(frozen=True)
class BeaconSnapshot:
    """Public-safe Atlas state used to detect real-time changes."""

    agents: Mapping[str, Mapping[str, object]]
    contracts: Mapping[str, Mapping[str, object]]


class BeaconRealtimeFeed:
    """Poll Beacon SQLite state and emit small, ordered delta events.

    The feed deliberately emits only fields already needed by the public Atlas
    visualization. Sensitive agent public keys, payment addresses, contract
    terms, amounts, and currency are not sent over the public WebSocket.
    """

    def __init__(self, db_path: str, poll_interval: float = 1.0):
        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")
        self.db_path = db_path
        self.poll_interval = float(poll_interval)
        self._sequence = 0

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_dict(row: sqlite3.Row, fields: Iterable[str]) -> Dict[str, object]:
        return {field: row[field] for field in fields}

    def snapshot(self) -> BeaconSnapshot:
        """Read a consistent public-safe snapshot from SQLite."""
        with self._connect() as conn:
            conn.execute("BEGIN")
            agent_rows = conn.execute(
                """SELECT agent_id, name, status, created_at, updated_at
                   FROM relay_agents
                   ORDER BY agent_id"""
            ).fetchall()
            contract_rows = conn.execute(
                """SELECT id, from_agent, to_agent, type, state, created_at, updated_at
                   FROM beacon_contracts
                   ORDER BY id"""
            ).fetchall()
            conn.commit()

        agents = {
            row["agent_id"]: self._row_dict(
                row, ("agent_id", "name", "status", "created_at", "updated_at")
            )
            for row in agent_rows
        }
        contracts = {
            row["id"]: {
                "id": row["id"],
                "from": row["from_agent"],
                "to": row["to_agent"],
                "type": row["type"],
                "state": row["state"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in contract_rows
        }
        return BeaconSnapshot(agents=agents, contracts=contracts)

    def _event(self, event_type: str, payload: Mapping[str, object]) -> Dict[str, object]:
        self._sequence += 1
        return {
            "v": 1,
            "seq": self._sequence,
            "type": event_type,
            "ts": int(time.time()),
            "data": dict(payload),
        }

    def diff(self, previous: BeaconSnapshot, current: BeaconSnapshot) -> List[Dict[str, object]]:
        """Return deterministic delta events between two snapshots."""
        events: List[Dict[str, object]] = []

        for agent_id in sorted(current.agents):
            now = current.agents[agent_id]
            before = previous.agents.get(agent_id)
            if before is None:
                events.append(self._event("agent.new", now))
                continue

            if now.get("status") != before.get("status") or now.get("name") != before.get("name"):
                events.append(self._event("agent.updated", now))
            elif now.get("updated_at") != before.get("updated_at"):
                events.append(
                    self._event(
                        "agent.heartbeat",
                        {
                            "agent_id": agent_id,
                            "status": now.get("status"),
                            "updated_at": now.get("updated_at"),
                        },
                    )
                )

        for agent_id in sorted(set(previous.agents) - set(current.agents)):
            events.append(self._event("agent.removed", {"agent_id": agent_id}))

        for contract_id in sorted(current.contracts):
            now = current.contracts[contract_id]
            before = previous.contracts.get(contract_id)
            if before is None:
                events.append(self._event("contract.new", now))
            elif dict(now) != dict(before):
                events.append(self._event("contract.updated", now))

        for contract_id in sorted(set(previous.contracts) - set(current.contracts)):
            events.append(self._event("contract.removed", {"id": contract_id}))

        return events

    def poll(self, stop_after: Optional[int] = None) -> Iterator[List[Dict[str, object]]]:
        """Yield non-empty event batches as the database changes."""
        previous = self.snapshot()
        cycles = 0
        while stop_after is None or cycles < stop_after:
            time.sleep(self.poll_interval)
            current = self.snapshot()
            events = self.diff(previous, current)
            previous = current
            cycles += 1
            if events:
                yield events


def stream_beacon_events(environ, db_path: str, poll_interval: float = 1.0):
    """Serve a one-way WebSocket stream until the client disconnects.

    ``simple-websocket`` supports WSGI servers. The public stream is read-only:
    it never accepts state-changing commands from clients.
    """
    try:
        from simple_websocket import ConnectionClosed, Server
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Beacon real-time feed requires simple-websocket; install project requirements"
        ) from exc

    ws = Server.accept(environ)
    feed = BeaconRealtimeFeed(db_path=db_path, poll_interval=poll_interval)
    initial = feed.snapshot()
    hello = {
        "v": 1,
        "seq": 0,
        "type": "hello",
        "ts": int(time.time()),
        "data": {
            "agents": len(initial.agents),
            "contracts": len(initial.contracts),
            "poll_interval_ms": int(poll_interval * 1000),
        },
    }

    try:
        ws.send(json.dumps(hello, separators=(",", ":")))
        previous = initial
        while True:
            time.sleep(poll_interval)
            current = feed.snapshot()
            for event in feed.diff(previous, current):
                ws.send(json.dumps(event, separators=(",", ":")))
            previous = current
    except ConnectionClosed:
        return ""
