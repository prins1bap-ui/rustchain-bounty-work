from __future__ import annotations

import json

import httpx
import pytest
from pydantic_ai import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from rustchain_pydanticai_agent_economy import (
    MarketplaceReadClient,
    MarketplaceTools,
    build_marketplace_agent,
)


def mock_transport() -> httpx.MockTransport:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/agent/jobs":
            return httpx.Response(200, json={"jobs": [{"job_id": "job_1", "reward_rtc": 75}]})
        if request.url.path == "/agent/jobs/job_1":
            return httpx.Response(200, json={"job_id": "job_1", "status": "open"})
        if request.url.path == "/agent/reputation/RTCabc":
            return httpx.Response(200, json={"trust_score": 94})
        if request.url.path == "/agent/stats":
            return httpx.Response(200, json={"total_jobs": 8})
        return httpx.Response(404, text="not found")

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_tool_methods_read_marketplace_data() -> None:
    async with MarketplaceReadClient("https://node.test", transport=mock_transport()) as client:
        tools = MarketplaceTools(client)
        jobs = json.loads(await tools.rustchain_browse_jobs(limit=5))
        detail = json.loads(await tools.rustchain_job_detail("job_1"))
        reputation = json.loads(await tools.rustchain_reputation("RTCabc"))
        stats = json.loads(await tools.rustchain_marketplace_stats())

    assert jobs["jobs"][0]["reward_rtc"] == 75
    assert detail["status"] == "open"
    assert reputation["trust_score"] == 94
    assert stats["total_jobs"] == 8


@pytest.mark.asyncio
async def test_invalid_inputs_fail_closed() -> None:
    async with MarketplaceReadClient("https://node.test", transport=mock_transport()) as client:
        with pytest.raises(ValueError):
            await client.get_job("../bad")
        with pytest.raises(ValueError):
            await client.browse_jobs(limit=0)
        with pytest.raises(ValueError):
            await client.browse_jobs(category="unknown")
        with pytest.raises(ValueError):
            await client.browse_jobs(min_reward=float("inf"))


@pytest.mark.asyncio
async def test_pydanticai_agent_registers_four_read_only_tools() -> None:
    captured: list[str] = []

    def inspect_tools(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        del messages
        captured.extend(tool.name for tool in info.function_tools)
        return ModelResponse(parts=[TextPart("schema inspected")])

    async with MarketplaceReadClient("https://node.test", transport=mock_transport()) as client:
        agent = build_marketplace_agent(client)
        result = await agent.run("Inspect the marketplace tool surface.", model=FunctionModel(inspect_tools))

    assert result.output == "schema inspected"
    assert set(captured) == {
        "rustchain_browse_jobs",
        "rustchain_job_detail",
        "rustchain_reputation",
        "rustchain_marketplace_stats",
    }
