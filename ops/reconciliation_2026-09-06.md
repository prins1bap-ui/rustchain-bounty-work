# RTC reconciliation — 2026-09-06

Authoritative maintainer adjudication received via Sophia Elya / Elyan Labs.

## Verified payout state

- Historical RECEIVED before current batch: 95 RTC.
- Current batch: 423 RTC in 31 pending rows, subject to maintainer-stated 24-hour hold.
- Do not count the 423 RTC as RECEIVED until authoritative release/cleared evidence appears.
- Potential lifetime RECEIVED after ordinary release: 518 RTC.
- Rolling 24h RECEIVED remains 0 as of latest check; rolling 24h PENDING_ON_CHAIN is 423 RTC.
- Gap to 500 rolling RECEIVED remains 500 until release. If the 423 clears inside the rolling window, the remaining gap becomes 77 RTC.

## Adjudicated items inside current batch

- #16471 payout-pipeline audit: 175 RTC.
- #685 Tier 1 Rust Agent Economy SDK: 50 RTC.
- #747 verifier partial credit: 40 RTC; remaining 35 requires actual bot integration.
- #14014 RustChain Ledger Exchange: 20 RTC.
- #14014 RustChain Antiquity Relay Yard: 20 RTC.
- #16497 tutorial 2 / long-form slot settlement: 33 RTC.
- #100 BOUNTY_HYGIENE improvement: 10 RTC.
- #2143 video-archive-manifest: 3 RTC.
- #2271 miner dry-run: 2 RTC.
- #398 Step 3 / Guardian: 40 RTC.
- Aug 29 small batch: 30 RTC total.
- #16601 Type A and other same-day accepted items were part of the maintainer's stated 423 RTC running total and must not be double-counted.

## Remaining concrete conversion opportunities

- #293 four music tracks: 28 RTC potential. Maintainer requires public OGG publication; each pays 7 RTC on sight.
- #177 two memes: 4 RTC potential. Maintainer requires public PNG publication; each pays 2 RTC on sight.
- #2259 article: 10 RTC potential, still blocked by 404 / external publication requirement.
- #747 remaining integration: 35 RTC potential, but requires actual bot integration and must be re-verified for live availability/competition before build.

These four opportunities total 77 RTC potential, exactly the residual needed after a 423 RTC release to reach 500 rolling RECEIVED, subject to availability, successful acceptance, and settlement timing.

## Exclusions

Future vulnerability hunting, exploit/red-team/security auditing, adversarial break-testing, auth bypass, privilege escalation, double-spend/fund attacks, fund creation, anti-fraud evasion, and any work requiring movement/signing/trading/staking/bridging of RTC or funds remain excluded.
