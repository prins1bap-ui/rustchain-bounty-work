# Bounty #16517 — Sega Genesis / BlastEm independent reproduction

Claimant: `@prins1bap-ui`  
RTC wallet: `RTCc5449fe1b93385961152720c864c0f073dae5855`

## Result

**DISAGREED, submitted for the 15 RTC independent-emulator tier.**

I independently measured the published Sega Genesis historical optimized figure on **BlastEm**, an emulator explicitly listed by #16517 as not used by the original project. The three runs were deterministic and the full 24-token output matched the host reference byte-for-byte.

I am **not** claiming the 33 RTC “published figure is wrong” tier from this result alone. The independent BlastEm measurement differs by about 1.667%, but that is not sufficient by itself to establish which emulator/instrument is responsible for the delta.

## Figure measured

Published historical target: **142,972,761 Motorola 68000 cycles** over the canonical 38-forward-pass benchmark interval.

Genesis source commit measured:

`6b5ce98e44bb07e9156291ffd470ff7371e170e9`

Commit description: `W16 index streams plus inner loop work: 1.543x on measured 68000 cycles`

The benchmark uses the canonical prompt plus 24 generated tokens.

## Independent emulator

- Emulator: **BlastEm 0.6.3-pre**
- Exact BlastEm commit: `b4d75247ebad8852fd9bc385b423df704c6c5af5`
- Runner: GitHub Actions, Ubuntu 24.04.5 LTS
- SGDK build environment: `ghcr.io/stephane-d/sgdk:latest`

## ROM provenance

Built from the exact historical Genesis engine commit above plus the repository benchmark harness.

Benchmark ROM SHA-256:

`428d19ef48f237b199fcbcfa10d978d308faacfc3287ff829a0e7e287550b6ff`

The generated symbol file placed `bench_marker` at CPU address `0xFF00AE`. The measurement code derives that address from `out/symbol.txt`; it is not hard-coded.

## Measurement method

BlastEm normally direct-maps Genesis work RAM in its JIT, so ordinary generic write helpers do not observe benchmark marker stores. For this measurement build, Genesis work-RAM **writes only** are routed through callbacks that preserve the same RAM contents while exposing the benchmark marker store. Reads remain direct-mapped.

At each marker write, the harness records BlastEm's internal `m68k_context->cycles` master-cycle counter. The measured 68000 cycle count is the master-cycle delta divided by the Genesis 68000 hardware divider of 7.

The timing markers surround the same benchmark interval as the published harness. Token evidence is emitted only after the END marker, so token reporting is outside the measured interval.

This is emulator-internal emulated timing, not host wall-clock timing.

## Raw measurements

| Run | BlastEm master-cycle delta | 68000 cycles |
|---|---:|---:|
| 1 | 1,017,491,328 | 145,355,904 |
| 2 | 1,017,491,328 | 145,355,904 |
| 3 | 1,017,491,328 | 145,355,904 |

Deterministic across all three runs: **YES**.

Comparison with published historical target:

- BlastEm: **145,355,904 cycles**
- Published MAME result: **142,972,761 cycles**
- Delta: **+2,383,143 cycles**
- Delta percentage: **+1.666851%**

## Correctness gate

All 24 generated greedy tokens matched the canonical host reference byte-for-byte:

```text
67,97,108,108,32,109,101,32,83,111,112,104,105,97,32,69,108,121,97,44,32,121,111,117
```

Decoded:

```text
Call me Sophia Elya, you
```

Gate: **24/24 PASS**.

## Reproduction evidence

Workflow:

`https://github.com/prins1bap-ui/rustchain-bounty-work/blob/bounty-16517-genesis-blastem-20260910/.github/workflows/bounty-16517-genesis-blastem.yml`

BlastEm instrumentation helper:

`https://github.com/prins1bap-ui/rustchain-bounty-work/blob/bounty-16517-genesis-blastem-20260910/16517-genesis-blastem/instrument_blastem.py`

Successful GitHub Actions run:

`https://github.com/prins1bap-ui/rustchain-bounty-work/actions/runs/34541997819`

Evidence artifact ID: `10177702757`  
Artifact SHA-256: `b31389c0c896fdfa3facb02da633909c4a5d11264876ec90b07868e8b13f4668`

The workflow fails closed if timing markers are absent, if any of the 24 tokens differ, if the master-cycle delta cannot be converted cleanly using the divider, or if repeated runs are non-deterministic.

## Claim

Requested tier: **15 RTC — reproduce a published figure on an emulator the project did not use.**

The result is a reproducible independent-emulator disagreement, but I am deliberately not asserting the 33 RTC correction tier without stronger evidence establishing that the published MAME result itself is wrong.
