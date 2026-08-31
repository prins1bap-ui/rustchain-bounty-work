# RustChain RIP-302 tools for PydanticAI

Bounty delivery for `Scottcjn/rustchain-bounties#685`, Tier 2 agent integration.

This package integrates the RIP-302 Agent Economy marketplace with PydanticAI using the framework's native `Agent(tools=[...])` function-tool registration surface.

It exposes four deliberately read-only tools:

- `rustchain_browse_jobs`
- `rustchain_job_detail`
- `rustchain_reputation`
- `rustchain_marketplace_stats`

The package contains no POST route implementation. It cannot post or claim jobs, submit deliverables, accept/dispute/cancel jobs, lock escrow, release escrow, or transfer RTC.

## Install

```bash
python -m pip install -e .
```

Python 3.10+ is required. QA pins `pydantic-ai==2.36.0`.

## Example

```python
from rustchain_pydanticai_agent_economy import MarketplaceReadClient, build_marketplace_agent

async with MarketplaceReadClient("https://50.28.86.131") as client:
    agent = build_marketplace_agent(client, model="openai:gpt-5-mini")
    result = await agent.run(
        "Find the highest-reward open code jobs and summarize them. Do not claim anything."
    )
    print(result.output)
```

A real model run requires the provider configuration normally required by PydanticAI. The deterministic test suite uses PydanticAI's `FunctionModel` to inspect the registered tool schema without making a model-provider call.

## Safety boundary

The #685 Tier 2 examples explicitly include marketplace browsing as an integration shape. This package keeps that boundary strict: GET-only marketplace observation and no fund-changing methods.

The client validates route segments, documented job status/category filters, reward filters, pagination bounds, HTTP response shape, and error handling before returning data to the agent.

## QA

```bash
python -m pip install -e '.[test]'
ruff check src tests
pytest -q
```

CI runs on Python 3.10 and 3.12.

## Sources

See [`SOURCES.md`](SOURCES.md).

## License

MIT.
