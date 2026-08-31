# Sources and verification basis

## RustChain bounty contract

- `Scottcjn/rustchain-bounties#685` — RIP-302 Agent Economy build bounties.
- Tier 2 pays 75 RTC per agent-framework integration. The issue gives a Grazer marketplace-browsing skill as an explicit example, which is the scope model for this GET-only integration.
- Documented read endpoints used here:
  - `GET /agent/jobs`
  - `GET /agent/jobs/<id>`
  - `GET /agent/reputation/<wallet>`
  - `GET /agent/stats`

Bounty URL: https://github.com/Scottcjn/rustchain-bounties/issues/685

## RustChain source snapshot

Implementation was checked against RustChain `main` at commit:

`71653f2287e2491225367f42b7053637b790b642`

Canonical RIP-302 source:

https://github.com/Scottcjn/Rustchain/blob/71653f2287e2491225367f42b7053637b790b642/rip302_agent_economy.py

No production mutation route was invoked while developing or testing this package.

## OpenAI Agents SDK

The integration follows the official Python Agents SDK `FunctionTool` / `function_tool` API. Official documentation says Python functions can be converted into agent tools with generated schemas and can be attached through an agent's `tools` collection.

- Tools documentation: https://openai.github.io/openai-agents-python/tools/
- SDK documentation: https://openai.github.io/openai-agents-python/
- QA dependency: `openai-agents==0.22.0`, released 2026-08-19 on PyPI.
- PyPI: https://pypi.org/project/openai-agents/0.22.0/

## Scope decision

The package exposes only the four documented GET surfaces above. POST routes remain outside this delivery so deterministic QA cannot accidentally move RTC, lock/release escrow, change job state, or create a transaction.
