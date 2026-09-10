# #16517 claim — Genesis / BlastEm independent reproduction

Claimant: @prins1bap-ui  
RTC wallet: RTCc5449fe1b93385961152720c864c0f073dae5855  
Requested tier: **15 RTC (different emulator)**

I independently re-measured the published Genesis optimized benchmark on BlastEm 0.6.3-pre (commit `b4d75247ebad8852fd9bc385b423df704c6c5af5`) against Genesis source commit `6b5ce98e44bb07e9156291ffd470ff7371e170e9`.

Raw results, three independent runs:

- 1,017,491,328 BlastEm master cycles = 145,355,904 68000 cycles
- 1,017,491,328 BlastEm master cycles = 145,355,904 68000 cycles
- 1,017,491,328 BlastEm master cycles = 145,355,904 68000 cycles

Published MAME count: 142,972,761 cycles. BlastEm is +2,383,143 cycles (+1.666851%). I am **not** claiming the 33 RTC correction tier from this alone; this is the 15 RTC independent-emulator tier.

Correctness gate: **24/24 PASS**, byte-identical to the host reference: `Call me Sophia Elya, you`.

Evidence report:
https://github.com/prins1bap-ui/rustchain-bounty-work/blob/bounty-16517-genesis-blastem-20260910/16517-genesis-blastem/REPORT.md

Successful workflow run:
https://github.com/prins1bap-ui/rustchain-bounty-work/actions/runs/34541997819

Evidence artifact: ID `10177702757`, SHA-256 `b31389c0c896fdfa3facb02da633909c4a5d11264876ec90b07868e8b13f4668`.

The harness derives the benchmark marker from generated symbols, records BlastEm's emulator-internal cycle counter at START/END, converts master cycles using the Genesis 68000 divider of 7, and fails closed for missing markers, token mismatch, non-integral conversion, or non-deterministic repeated runs.
