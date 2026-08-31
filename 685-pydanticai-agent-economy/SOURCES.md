# Sources and verification basis

## RustChain bounty

- `Scottcjn/rustchain-bounties#685` — RIP-302 Agent Economy build bounties.
- Tier 2 lists agent-framework integrations at 75 RTC each and gives a Grazer marketplace-browsing skill as an explicit example.
- Read endpoints used here:
  - `GET /agent/jobs`
  - `GET /agent/jobs/<id>`
  - `GET /agent/reputation/<wallet>`
  - `GET /agent/stats`

Bounty: https://github.com/Scottcjn/rustchain-bounties/issues/685

## RustChain source snapshot

Checked against RustChain `main` commit:

`71653f2287e2491225367f42b7053637b790b642`

Canonical implementation:

https://github.com/Scottcjn/Rustchain/blob/71653f2287e2491225367f42b7053637b790b642/rip302_agent_economy.py

## PydanticAI

Official PydanticAI function-tool documentation documents three native registration paths, including passing plain functions through `Agent(tools=[...])`. It also documents `FunctionModel` for deterministic inspection/testing of registered tool schemas.

- Function tools: https://pydantic.dev/docs/ai/tools-toolsets/tools/
- PyPI: https://pypi.org/project/pydantic-ai/
- QA dependency: `pydantic-ai==2.36.0` (released 2026-08-29).

## Safety

No production POST endpoint or fund-changing operation was invoked. The package does not implement RIP-302 mutation routes.
