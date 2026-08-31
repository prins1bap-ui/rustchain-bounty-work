"""OpenAI Agents SDK function tools for read-only RIP-302 marketplace access."""

from __future__ import annotations

import json

from agents import FunctionTool, function_tool

from .client import AgentEconomyReadClient


class MarketplaceToolset:
    """Build a bounded, GET-only tool surface for an OpenAI Agents SDK agent."""

    def __init__(self, client: AgentEconomyReadClient) -> None:
        self.client = client

    async def browse_jobs(
        self,
        status: str | None = "open",
        category: str | None = None,
        min_reward: float | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> str:
        payload = await self.client.browse_jobs(
            status=status,
            category=category,
            min_reward=min_reward,
            limit=limit,
            offset=offset,
        )
        return json.dumps(payload, sort_keys=True)

    async def job_detail(self, job_id: str) -> str:
        return json.dumps(await self.client.get_job(job_id), sort_keys=True)

    async def reputation(self, wallet: str) -> str:
        return json.dumps(await self.client.get_reputation(wallet), sort_keys=True)

    async def stats(self) -> str:
        return json.dumps(await self.client.get_stats(), sort_keys=True)

    def as_agent_tools(self) -> list[FunctionTool]:
        """Return four OpenAI Agents SDK FunctionTool objects."""

        @function_tool(name_override="rustchain_browse_jobs")
        async def browse_jobs(
            status: str | None = "open",
            category: str | None = None,
            min_reward: float | None = None,
            limit: int = 20,
            offset: int = 0,
        ) -> str:
            """Browse RIP-302 marketplace jobs without claiming or changing them.

            Args:
                status: Optional lifecycle status, normally open.
                category: Optional documented RIP-302 job category.
                min_reward: Optional minimum RTC reward filter.
                limit: Number of jobs to request, from 1 through 100.
                offset: Non-negative pagination offset.
            """
            return await self.browse_jobs(status, category, min_reward, limit, offset)

        @function_tool(name_override="rustchain_job_detail")
        async def job_detail(job_id: str) -> str:
            """Read one RIP-302 job including its server-provided detail and activity data.

            Args:
                job_id: Marketplace job identifier.
            """
            return await self.job_detail(job_id)

        @function_tool(name_override="rustchain_reputation")
        async def reputation(wallet: str) -> str:
            """Read the RIP-302 reputation record for a wallet or miner identifier.

            Args:
                wallet: Wallet or miner identifier accepted by the marketplace endpoint.
            """
            return await self.reputation(wallet)

        @function_tool(name_override="rustchain_marketplace_stats")
        async def marketplace_stats() -> str:
            """Read the RIP-302 marketplace overview statistics."""
            return await self.stats()

        return [browse_jobs, job_detail, reputation, marketplace_stats]
