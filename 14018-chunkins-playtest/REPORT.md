# CHUNKINS #14018 Playtest Report — @prins1bap-ui

**Bounty:** Scottcjn/rustchain-bounties#14018  
**RTC payout wallet:** `RTCc5449fe1b93385961152720c864c0f073dae5855`  
**Feverdream source commit tested:** `380e133ac7be681d99d6f2a496376db7ab15825d`  
**Execution run:** https://github.com/prins1bap-ui/rustchain-bounty-work/actions/runs/34376783009

## Environment

- GitHub-hosted Ubuntu 24.04 runner
- Linux 6.17.0-1022-azure x86_64
- AMD EPYC 7763 64-Core Processor presented to the runner
- CPU rendering path; no CUDA/GPU post-processing
- SDL dummy/headless game path
- Real `fd-daemon`, `fd-game`, POV-Ray renderer, and Lua world logic; no stubbed renderer

The workflow cloned the current `Scottcjn/feverdream-engine`, built POV-Ray and the resident renderer, explicitly built `fd-daemon`, built `fd-game`, ran the repository's official verification suite, and then ran eight separate 240-frame CHUNKINS gametests.

## Official verification suite

The repository's complete `game/test.sh` suite passed, including engine regression, RELIC SWEEP, CRATE CLIMB, CHUNKINS worlds 1/4/5/6/7, Bridge Garden, sandbox restrictions, and level-chain transition. GPU post math was skipped because no CUDA library was built. Final result: **ALL TESTS PASS**.

## Measured CHUNKINS results

| World | Script | FPS | Score | Lives | Highest stand | Result |
|---|---|---:|---:|---:|---:|---|
| 1 — Acorn Meadow | `chunkins1.lua` | 35.0 | 1 | 3 | 1.00 | real frame, Lua logic live |
| 2 — Crate Heights | `chunkins2.lua` | 34.6 | 1 | 3 | 1.00 | real frame, Lua logic live |
| 3 — Acorn Mountain | `chunkins3.lua` | 37.6 | 1 | 3 | 0.00 | real frame, Lua logic live |
| 4 — Thief's Hollow | `chunkins4.lua` | 33.9 | 1 | 3 | 0.00 | real frame, Lua logic live |
| 5 — Windmill Pass | `chunkins5.lua` | 32.8 | 1 | 3 | 0.00 | real frame, Lua logic live |
| 6 — Hazelnut Bridges | `chunkins_hazelnut_bridges.lua` | 32.8 | 2 | 3 | 0.66 | real frame, Lua logic live |
| 7 — Cascade Hollow | `chunkins7.lua` | 14.2 | 2 | 3 | 0.00 | real frame, Lua logic live |
| Bonus — Bridge Garden | `chunkins_bridge_garden.lua` | 33.8 | 3 | 3 | 1.45 | real frame, Lua logic live |

Arithmetic mean across these eight runs: **31.84 FPS**. Every run reported `pixels: REAL FRAME (non-uniform 320x180)` and `GAME LOGIC LIVE`.

## Concrete observations

1. **Cascade Hollow is a large CPU-performance outlier on this runner.** World 7 measured **14.2 FPS**, while the other seven runs ranged from 32.8 to 37.6 FPS. That puts Cascade Hollow roughly 57% below the mean of the other seven. The world still remained playable by the automated harness and collected two items, so this looks like a scene/render-cost issue rather than dead game logic.

2. **Bridge Garden provides the strongest immediate automated reward/progression signal in this build.** It reached score 3 and highest stand 1.45 in the same 240-frame path, compared with score 1 and stand 0.00 in worlds 3, 4, and 5. Its opening geometry therefore appears substantially easier for the simple forward/jump path to read and traverse.

3. **Worlds 3, 4, and 5 all collect an item but show no vertical stand progress.** That consistency suggests the early route can reward the player without clearly teaching upward/platform progression. The level logic is live, but the opening traversal signal is weaker than worlds 1/2, Hazelnut Bridges, and Bridge Garden.

4. **Hazelnut Bridges remains a strong early-feedback world.** It reached score 2 and highest stand 0.66 while holding essentially the same FPS as Windmill Pass. That makes it a useful reference for tuning difficulty without increasing render cost.

5. **Audio initialization was clean across every tested world.** Each run reported `audio open — 5/5 sfx from assets, rest synthesized`, so the headless path exercised the audio hooks without blocking or asset-load failure.

## What I would change in World 5

Windmill Pass should borrow the immediate route readability of Bridge Garden/Hazelnut Bridges. I would put one unmistakable windmill landmark and a guaranteed first vertical step/platform directly on the opening forward lane, then introduce the timing-sensitive moving geometry. The current automated path earns one pickup but stays at `highest stand 0.00`, so the opening teaches collection better than vertical navigation.

## Reproduction

The exact autonomous workflow used for this report is committed in this repository at `.github/workflows/chunkins-playtest-14018.yml` on branch `chunkins-playtest-20260909`. The successful run is linked above and retained the build, official-suite, per-world, daemon, environment/source-commit evidence as a GitHub Actions artifact.

AI-assisted execution and analysis disclosed. No acceptance, payout, pending transfer, or received RTC is asserted until the maintainer adjudicates the report and authoritative wallet evidence confirms any transfer.
