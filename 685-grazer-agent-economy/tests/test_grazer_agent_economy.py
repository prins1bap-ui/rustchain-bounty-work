import json

import pytest

from grazer_agent_economy import AgentEconomyGrazer


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status = status

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.headers = {}

    def get(self, url, params=None, timeout=None):
        self.calls.append(("GET", url, params, timeout))
        if not self.responses:
            raise AssertionError("unexpected GET")
        return FakeResponse(self.responses.pop(0))


def sample_job(**overrides):
    job = {
        "job_id": "job_abc123",
        "poster_wallet": "poster",
        "worker_wallet": None,
        "title": "Write a concise API guide",
        "description": "Document the read-only marketplace discovery endpoints.",
        "category": "writing",
        "reward_rtc": 50.0,
        "status": "open",
        "created_at": 1788090000,
        "expires_at": 1788694800,
        "tags": json.dumps(["docs", "rip-302"]),
    }
    job.update(overrides)
    return job


def test_discover_normalizes_grazer_fields_and_only_gets():
    session = FakeSession([{"ok": True, "jobs": [sample_job()], "total": 1}])
    client = AgentEconomyGrazer("https://node.example", session=session)

    jobs = client.discover(category="writing", min_reward=25, limit=500)

    assert len(jobs) == 1
    job = jobs[0]
    assert job["id"] == "job_abc123"
    assert job["platform"] == "rustchain-agent-economy"
    assert job["author"] == "poster"
    assert job["content"].startswith("Document the")
    assert job["tags"] == ["docs", "rip-302"]
    assert job["canonical_url"] == "https://node.example/agent/jobs/job_abc123"
    assert session.calls == [(
        "GET",
        "https://node.example/agent/jobs",
        {"status": "open", "min_reward": 25.0, "limit": 100, "offset": 0, "category": "writing"},
        15,
    )]


def test_detail_preserves_activity_log_and_ratings():
    raw = sample_job(
        status="completed",
        activity_log=[{"action": "posted", "created_at": 1}],
        ratings=[{"rating": 5}],
        deliverable_url="https://example.com/work",
    )
    session = FakeSession([{"ok": True, "job": raw}])
    client = AgentEconomyGrazer("https://node.example", session=session)

    job = client.job("job_abc123")

    assert job["status"] == "completed"
    assert job["activity_log"][0]["action"] == "posted"
    assert job["ratings"][0]["rating"] == 5
    assert job["deliverable_url"] == "https://example.com/work"


def test_reputation_unwraps_record():
    session = FakeSession([{
        "ok": True,
        "wallet_id": "alice",
        "reputation": {"trust_score": 92, "trust_level": "legendary"},
    }])
    client = AgentEconomyGrazer("https://node.example", session=session)

    rep = client.reputation("alice")

    assert rep == {"trust_score": 92, "trust_level": "legendary", "wallet_id": "alice"}


def test_reputation_handles_no_history():
    session = FakeSession([{
        "ok": True,
        "wallet_id": "new-agent",
        "reputation": None,
        "message": "No reputation history",
    }])
    client = AgentEconomyGrazer("https://node.example", session=session)

    rep = client.reputation("new-agent")

    assert rep["reputation"] is None
    assert rep["wallet_id"] == "new-agent"


def test_stats_unwraps_server_stats():
    session = FakeSession([{
        "ok": True,
        "stats": {"total_jobs": 86, "open_jobs": 4, "total_rtc_volume": 544.0},
    }])
    client = AgentEconomyGrazer("https://node.example", session=session)

    assert client.stats()["total_jobs"] == 86


def test_search_is_local_and_keeps_reward_order():
    jobs = [
        sample_job(job_id="job_high", reward_rtc=75, title="RustChain code review", category="code"),
        sample_job(job_id="job_low", reward_rtc=30, title="Write docs", category="writing"),
    ]
    session = FakeSession([{"ok": True, "jobs": jobs, "total": 2}])
    client = AgentEconomyGrazer("https://node.example", session=session)

    matches = client.search("rustchain", min_reward=20, limit=5)

    assert [j["job_id"] for j in matches] == ["job_high"]
    assert session.calls[0][2]["limit"] == 100


def test_high_value_maps_to_open_min_reward():
    session = FakeSession([{"ok": True, "jobs": [], "total": 0}])
    client = AgentEconomyGrazer("https://node.example", session=session)

    assert client.high_value(min_reward=50) == []
    params = session.calls[0][2]
    assert params["status"] == "open"
    assert params["min_reward"] == 50.0


def test_invalid_inputs_fail_before_network():
    session = FakeSession([])
    client = AgentEconomyGrazer("https://node.example", session=session)

    with pytest.raises(ValueError):
        client.discover(status="not-a-status")
    with pytest.raises(ValueError):
        client.discover(category="not-a-category")
    with pytest.raises(ValueError):
        client.discover(min_reward=-1)
    with pytest.raises(ValueError):
        client.job("")
    with pytest.raises(ValueError):
        client.reputation("")
    assert session.calls == []


def test_non_object_json_fails_closed():
    session = FakeSession([["unexpected", "array"]])
    client = AgentEconomyGrazer("https://node.example", session=session)

    with pytest.raises(ValueError, match="non-object JSON"):
        client.stats()


def test_read_only_surface_has_no_mutating_methods():
    forbidden = {
        "post_job", "claim_job", "deliver_job", "accept_delivery",
        "dispute_job", "cancel_job", "transfer", "tip", "bridge",
    }
    public = {name for name in dir(AgentEconomyGrazer) if not name.startswith("_")}
    assert forbidden.isdisjoint(public)
