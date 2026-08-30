# RustChain Agent Economy → Grazer integration

A **read-only Grazer discovery plugin** for the RustChain RIP-302 Agent Economy. This targets the explicit Tier 2 example in RustChain bounty **#685**: “Grazer skill for job marketplace browsing.”

The module mirrors Grazer's existing platform-client pattern (`BoTTubeGrazer`) and maps RIP-302 jobs into dictionaries with Grazer-friendly `title`, `content`, `author`, `creator`, `created_at`, `url`, and `canonical_url` fields while preserving marketplace metadata such as reward, status, category, tags, and wallets.

## Why this is deliberately read-only

Grazer is a discovery layer. This integration therefore exposes only the four public GET surfaces needed for discovery and reputation context:

- `GET /agent/jobs`
- `GET /agent/jobs/<job_id>`
- `GET /agent/reputation/<wallet_id>`
- `GET /agent/stats`

There are **no methods for posting jobs, claiming jobs, delivering work, accepting deliveries, disputing/cancelling jobs, moving RTC, signing transactions, tipping, or bridging**.

## Source baseline

Verified against current public source on **2026-08-30**:

- RustChain `main`: `71653f2287e2491225367f42b7053637b790b642`
- RIP-302 implementation: `rip302_agent_economy.py`
- Grazer `main`: `629fc62668f9fc249c9313bb3b1cd82ff492e89b`
- Grazer reference client: `grazer/bottube_grazer.py`

The current RIP-302 source orders `/agent/jobs` by `reward_rtc DESC, created_at DESC`, caps `limit` at 100, and returns the fields normalized here. The plugin preserves that ordering rather than inventing its own ranking.

## Install

This standalone delivery only needs Python and `requests`:

```bash
python -m pip install requests
```

If you already use Grazer:

```bash
python -m pip install grazer-skill
```

## Use as a Grazer-style Python source

```python
from grazer_agent_economy import AgentEconomyGrazer

client = AgentEconomyGrazer()

# Browse the highest-value open work first.
for job in client.high_value(min_reward=25, limit=10):
    print(job["reward_rtc"], job["title"], job["canonical_url"])

# Filter to a normal RIP-302 category.
code_jobs = client.discover(category="code", min_reward=5, limit=20)

# Read public reputation context without modifying anything.
rep = client.reputation("some-wallet")
```

## CLI

```bash
python grazer_agent_economy.py high-value --min-reward 25 --limit 10
python grazer_agent_economy.py jobs --category writing --min-reward 5
python grazer_agent_economy.py search "documentation" --min-reward 1
python grazer_agent_economy.py job job_abc123
python grazer_agent_economy.py reputation some-wallet
python grazer_agent_economy.py stats
```

The node is configurable for deployments that expose RIP-302 somewhere other than the historical Node 1 address:

```bash
python grazer_agent_economy.py --node https://your-rustchain-node.example jobs
```

## Grazer normalization

A RIP-302 job such as:

```json
{
  "job_id": "job_abc123",
  "poster_wallet": "poster",
  "title": "Write a concise API guide",
  "description": "Document the marketplace discovery endpoints.",
  "category": "writing",
  "reward_rtc": 50,
  "status": "open",
  "created_at": 1788090000,
  "expires_at": 1788694800,
  "tags": "[\"docs\", \"rip-302\"]"
}
```

is normalized to include:

```json
{
  "id": "job_abc123",
  "platform": "rustchain-agent-economy",
  "title": "Write a concise API guide",
  "content": "Document the marketplace discovery endpoints.",
  "author": "poster",
  "creator": "poster",
  "reward_rtc": 50,
  "category": "writing",
  "status": "open",
  "tags": ["docs", "rip-302"]
}
```

That shape intentionally overlaps Grazer's canonical content/creator/timestamp/url fields so existing discovery, de-duplication, scoring, and export code can consume the records with minimal glue.

## QA

```bash
python -m py_compile grazer_agent_economy.py
pytest -q
```

Expected result for this delivery:

```text
10 passed
```

Tests verify:

- Grazer-field normalization
- reward/category/status query forwarding
- server limit cap compatibility
- job detail/activity/rating preservation
- reputation and no-history handling
- marketplace stats unwrapping
- local free-text search over public browse results
- high-value discovery behavior
- invalid-input fail-closed behavior
- a read-only public surface with no mutating Agent Economy methods

## Deployment note

The historical public Node 1 URL in #685 is retained as the default because it is still the canonical base in the current bounty/source documentation. Operators can override `--node` / `base_url` without changing the integration. No claim here is made that a particular deployment endpoint is currently reachable from every network.

## Bounty

- Target: `Scottcjn/rustchain-bounties#685`
- Tier: **Tier 2 — Agent Integration (75 RTC each)**
- Explicit target lane: **Grazer skill for job marketplace browsing**
- Claimant: `prins1bap-ui`
- RTC wallet: `RTCc5449fe1b93385961152720c864c0f073dae5855`
