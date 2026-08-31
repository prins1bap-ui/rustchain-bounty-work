"""Factory for a read-only RIP-302 marketplace agent."""

from __future__ import annotations

from agents import Agent

from .client import AgentEconomyReadClient
from .tools import MarketplaceToolset


INSTRUCTIONS = """You are a RustChain Agent Economy marketplace observer.
Use the provided tools to discover jobs, inspect job details, read reputation, and summarize
marketplace statistics. The tool surface is intentionally read-only. Never imply that you claimed,
posted, delivered, accepted, disputed, cancelled, funded, transferred, or otherwise changed a job
or RTC balance. Clearly separate server-returned facts from your own analysis.
"""


def build_marketplace_agent(
    client: AgentEconomyReadClient,
    *,
    name: str = "RustChain Marketplace Observer",
    model: str | None = None,
) -> Agent:
    """Create an OpenAI Agents SDK Agent with four GET-only marketplace tools."""
    kwargs = {
        "name": name,
        "instructions": INSTRUCTIONS,
        "tools": MarketplaceToolset(client).as_agent_tools(),
    }
    if model is not None:
        kwargs["model"] = model
    return Agent(**kwargs)
