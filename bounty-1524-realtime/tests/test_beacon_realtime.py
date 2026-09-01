import os
import sqlite3
import tempfile
import unittest

from node.beacon_realtime import BeaconRealtimeFeed


SCHEMA = """
CREATE TABLE relay_agents (
    agent_id TEXT PRIMARY KEY,
    pubkey_hex TEXT NOT NULL,
    name TEXT,
    status TEXT DEFAULT 'active',
    coinbase_address TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER
);
CREATE TABLE beacon_contracts (
    id TEXT PRIMARY KEY,
    from_agent TEXT NOT NULL,
    to_agent TEXT,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'RTC',
    term TEXT NOT NULL,
    state TEXT DEFAULT 'offered',
    created_at INTEGER NOT NULL,
    updated_at INTEGER
);
"""


class RealtimeFeedTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        with sqlite3.connect(self.path) as conn:
            conn.executescript(SCHEMA)
        self.feed = BeaconRealtimeFeed(self.path, poll_interval=0.001)

    def tearDown(self):
        os.unlink(self.path)

    def mutate(self, sql, args=()):
        with sqlite3.connect(self.path) as conn:
            conn.execute(sql, args)
            conn.commit()

    def event_types(self, before, after):
        return [event['type'] for event in self.feed.diff(before, after)]

    def test_new_agent_and_contract_are_emitted(self):
        before = self.feed.snapshot()
        self.mutate(
            "INSERT INTO relay_agents VALUES (?, ?, ?, ?, ?, ?, ?)",
            ('bcn_1', 'aa', 'Agent One', 'active', '0xsecret', 10, 10),
        )
        self.mutate(
            "INSERT INTO beacon_contracts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ('ctr_1', 'bcn_1', 'bcn_2', 'rent', 99.0, 'RTC', 'PRIVATE TERM', 'offered', 10, 10),
        )
        after = self.feed.snapshot()
        events = self.feed.diff(before, after)
        self.assertEqual([e['type'] for e in events], ['agent.new', 'contract.new'])
        serialized = repr(events)
        self.assertNotIn('0xsecret', serialized)
        self.assertNotIn('PRIVATE TERM', serialized)
        self.assertNotIn('99.0', serialized)

    def test_heartbeat_is_distinct_from_profile_update(self):
        self.mutate(
            "INSERT INTO relay_agents VALUES (?, ?, ?, ?, ?, ?, ?)",
            ('bcn_1', 'aa', 'Agent One', 'active', None, 10, 10),
        )
        before = self.feed.snapshot()
        self.mutate("UPDATE relay_agents SET updated_at = 11 WHERE agent_id = 'bcn_1'")
        after = self.feed.snapshot()
        events = self.feed.diff(before, after)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['type'], 'agent.heartbeat')
        self.assertEqual(events[0]['data']['agent_id'], 'bcn_1')

    def test_profile_and_contract_updates_emit_once(self):
        self.mutate(
            "INSERT INTO relay_agents VALUES (?, ?, ?, ?, ?, ?, ?)",
            ('bcn_1', 'aa', 'Agent One', 'active', None, 10, 10),
        )
        self.mutate(
            "INSERT INTO beacon_contracts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ('ctr_1', 'bcn_1', 'bcn_2', 'rent', 1.0, 'RTC', 'term', 'offered', 10, 10),
        )
        before = self.feed.snapshot()
        self.mutate("UPDATE relay_agents SET status='inactive', updated_at=20 WHERE agent_id='bcn_1'")
        self.mutate("UPDATE beacon_contracts SET state='active', updated_at=20 WHERE id='ctr_1'")
        after = self.feed.snapshot()
        self.assertEqual(self.event_types(before, after), ['agent.updated', 'contract.updated'])

    def test_removed_objects_emit_tombstones(self):
        self.mutate(
            "INSERT INTO relay_agents VALUES (?, ?, ?, ?, ?, ?, ?)",
            ('bcn_1', 'aa', 'Agent One', 'active', None, 10, 10),
        )
        self.mutate(
            "INSERT INTO beacon_contracts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ('ctr_1', 'bcn_1', 'bcn_2', 'rent', 1.0, 'RTC', 'term', 'offered', 10, 10),
        )
        before = self.feed.snapshot()
        self.mutate("DELETE FROM beacon_contracts WHERE id='ctr_1'")
        self.mutate("DELETE FROM relay_agents WHERE agent_id='bcn_1'")
        after = self.feed.snapshot()
        self.assertEqual(self.event_types(before, after), ['agent.removed', 'contract.removed'])

    def test_sequence_is_monotonic(self):
        before = self.feed.snapshot()
        self.mutate(
            "INSERT INTO relay_agents VALUES (?, ?, ?, ?, ?, ?, ?)",
            ('bcn_2', 'aa', 'B', 'active', None, 10, 10),
        )
        self.mutate(
            "INSERT INTO relay_agents VALUES (?, ?, ?, ?, ?, ?, ?)",
            ('bcn_1', 'bb', 'A', 'active', None, 10, 10),
        )
        after = self.feed.snapshot()
        events = self.feed.diff(before, after)
        self.assertEqual([e['seq'] for e in events], [1, 2])
        self.assertEqual([e['data']['agent_id'] for e in events], ['bcn_1', 'bcn_2'])


if __name__ == '__main__':
    unittest.main()
