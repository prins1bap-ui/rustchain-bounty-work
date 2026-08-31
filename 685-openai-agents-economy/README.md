# RustChain RIP-302 tools for the OpenAI Agents SDK

Bounty delivery for `Scottcjn/rustchain-bounties#685`, Tier 2 agent integration.

This package gives an OpenAI Agents SDK agent a deliberately **read-only** view of the RIP-302 Agent Economy marketplace. It exposes four `FunctionTool` objects:

- `rustchain_browse_jobs` — browse jobs with documented status/category/reward/pagination filters
- `rustchain_job_detail` — read one job and the server-provided activity/detail payload
- `rustchain_reputation` — read a wallet's marketplace reputation
- `rustchain_marketplace_stats` — read marketplace-wide statistics

No POST endpoint is implemented. The integration cannot post, claim, deliver, accept, dispute, cancel, fund escrow, or transfer RTC.

## Install

```bash
python -m pip install -e .
```

Python 3.10+ is required. The package pins the current OpenAI Agents SDK release used for QA (`openai-agents==0.22.0`).

## Use

```python
from agents import Runner
from rustchain_openai_agents_economy import AgentEconomyReadClient, build_marketplace_agent

async with AgentEconomyReadClient("https://50.28.86.131") as client:
    agent = build_marketplace_agent(client)
    result = await Runner.run(
        agent,
        "Find the highest-reward open code jobs and summarize the top three. Do not claim anything.",
    )
    print(result.final_output)
```

Running an actual model call requires the normal OpenAI Agents SDK model configuration. The integration itself does not require a model or API key for its deterministic client/tool tests.

## Safety boundary

This contribution is intentionally narrower than a full transaction client. The bounty's Grazer example establishes marketplace browsing as a valid integration shape, and this implementation follows that non-mutating pattern for the OpenAI Agents SDK.

The client validates job/wallet path segments and documented filters before network access, bounds pagination, rejects non-finite rewards, rejects non-object JSON responses, and preserves a bounded portion of unsuccessful response bodies for diagnostics.

## QA

```bash
python -m pip install -e '.[test]'
ruff check src tests
pytest -q
```

GitHub Actions runs the same checks on Python 3.10 and 3.12.

## Sources

See [`SOURCES.md`](SOURCES.md) for the exact RustChain source commit, bounty contract, and OpenAI Agents SDK references used for this delivery.

## License

MIT. See [`LICENSE`](LICENSE).
