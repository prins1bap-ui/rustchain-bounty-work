"""PydanticAI integration for the read-only RIP-302 marketplace surface."""

import json

from pydantic_ai import Agent

from .client import MarketplaceReadClient

INSTRUCTIONS = """You observe the RustChain RIP-302 Agent Economy marketplace.
Use the registered tools to browse jobs, inspect details, read reputation, and summarize stats.
The integration is read-only. Never claim that you posted, claimed, delivered, accepted, disputed,
cancelled, funded, transferred, or otherwise changed RTC balances or marketplace state.
"""


class MarketplaceTools:
    """Reusable PydanticAI plain-function tools bound to a GET-only client."""

    def __init__(self, client: MarketplaceReadClient) -> None:
        self.client = client

    async def rustchain_browse_jobs(
        self,
        status: str | None = "open",
        category: str | None = None,
        min_reward: float | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> str:
        """Browse RIP-302 jobs without changing marketplace state."""
        payload = await self.client.browse_jobs(
            status=status,
            category=category,
            min_reward=min_reward,
            limit=limit,
            offset=offset,
        )
        return json.dumps(payload, sort_keys=True)

    async def rustchain_job_detail(self, job_id: str) -> str:
        """Read one RIP-302 job and its server-provided detail payload."""
        return json.dumps(await self.client.get_job(job_id), sort_keys=True)

    async def rustchain_reputation(self, wallet: str) -> str:
        """Read a wallet or miner's RIP-302 marketplace reputation."""
        return json.dumps(await self.client.get_reputation(wallet), sort_keys=True)

    async def rustchain_marketplace_stats(self) -> str:
        """Read RIP-302 marketplace-wide statistics."""
        return json.dumps(await self.client.get_stats(), sort_keys=True)

    def functions(self) -> list:
        """Return the four bound functions registered with PydanticAI."""
        return [
            self.rustchain_browse_jobs,
            self.rustchain_job_detail,
            self.rustchain_reputation,
            self.rustchain_marketplace_stats,
        ]


def build_marketplace_agent(
    client: MarketplaceReadClient,
    *,
    model: str | None = None,
) -> Agent:
    """Create a PydanticAI Agent with four GET-only RIP-302 tools."""
    kwargs = {
        "instructions": INSTRUCTIONS,
        "tools": MarketplaceTools(client).functions(),
    }
    if model is not None:
        kwargs["model"] = model
    return Agent(**kwargs)
