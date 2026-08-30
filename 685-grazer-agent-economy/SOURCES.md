# Sources

All implementation claims are tied to public repository source rather than inferred from marketing copy.

## RustChain Agent Economy

- Bounty #685 — Tier 2 explicitly lists “Grazer skill for job marketplace browsing” at 75 RTC:
  https://github.com/Scottcjn/rustchain-bounties/issues/685
- RIP-302 source at RustChain main commit `71653f2287e2491225367f42b7053637b790b642`:
  https://github.com/Scottcjn/Rustchain/blob/71653f2287e2491225367f42b7053637b790b642/rip302_agent_economy.py

Source-backed read routes used by this integration:

- `GET /agent/jobs`
- `GET /agent/jobs/<job_id>`
- `GET /agent/reputation/<wallet_id>`
- `GET /agent/stats`

`/agent/jobs` source-backed parameters and behavior:

- `status` defaults to `open`
- optional `category`
- `min_reward` is non-negative
- `limit` defaults to 50 and caps at 100
- `offset` is non-negative
- server ordering is `reward_rtc DESC, created_at DESC`

## Grazer

- Grazer main commit `629fc62668f9fc249c9313bb3b1cd82ff492e89b`:
  https://github.com/Scottcjn/grazer-skill/tree/629fc62668f9fc249c9313bb3b1cd82ff492e89b
- Existing platform-client pattern used as implementation reference:
  https://github.com/Scottcjn/grazer-skill/blob/629fc62668f9fc249c9313bb3b1cd82ff492e89b/grazer/bottube_grazer.py
- Grazer canonical normalizer fields (`title`, `content`, creator fields, timestamps, URL fields):
  https://github.com/Scottcjn/grazer-skill/blob/629fc62668f9fc249c9313bb3b1cd82ff492e89b/grazer/__init__.py

## Scope boundary

This delivery does not use or expose any RIP-302 POST route. It does not post/claim/deliver/accept jobs and does not move RTC. That is an intentional safety and product-design boundary: this is the bounty's **marketplace browsing** integration, not a payment executor.
