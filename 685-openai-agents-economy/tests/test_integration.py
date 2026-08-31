from __future__ import annotations

import httpx
import pytest
from agents import FunctionTool

from rustchain_openai_agents_economy import AgentEconomyReadClient, MarketplaceToolset


def mock_transport():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/agent/jobs":
            return httpx.Response(200, json={"jobs": [{"job_id": "job_1", "reward_rtc": 75}]})
        if request.url.path == "/agent/jobs/job_1":
            return httpx.Response(200, json={"job_id": "job_1", "status": "open"})
        if request.url.path == "/agent/reputation/RTCabc":
            return httpx.Response(200, json={"trust_score": 91})
        if request.url.path == "/agent/stats":
            return httpx.Response(200, json={"total_jobs": 7})
        return httpx.Response(404, text="not found")

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_read_methods():
    async with AgentEconomyReadClient("https://example.test", transport=mock_transport()) as client:
        jobs = await client.browse_jobs(limit=5)
        detail = await client.get_job("job_1")
        reputation = await client.get_reputation("RTCabc")
        stats = await client.get_stats()
    assert jobs["jobs"][0]["job_id"] == "job_1"
    assert detail["status"] == "open"
    assert reputation["trust_score"] == 91
    assert stats["total_jobs"] == 7


@pytest.mark.asyncio
async def test_validation_fails_closed():
    async with AgentEconomyReadClient("https://example.test", transport=mock_transport()) as client:
        with pytest.raises(ValueError):
            await client.get_job("../bad")
        with pytest.raises(ValueError):
            await client.browse_jobs(limit=0)
        with pytest.raises(ValueError):
            await client.browse_jobs(min_reward=float("nan"))


def test_openai_agents_tool_surface():
    client = AgentEconomyReadClient("https://example.test", transport=mock_transport())
    tools = MarketplaceToolset(client).as_agent_tools()
    assert all(isinstance(tool, FunctionTool) for tool in tools)
    assert {tool.name for tool in tools} == {
        "rustchain_browse_jobs",
        "rustchain_job_detail",
        "rustchain_reputation",
        "rustchain_marketplace_stats",
    }
