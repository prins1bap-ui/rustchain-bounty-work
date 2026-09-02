# Source Map

All technical claims are locked to public RustChain source commit:

`5a9d6a8a190008446d4f6c5ed2358bde532ba325` (Scottcjn/Rustchain `main`, verified 2026-09-02)

## S1 — Project description and multiplier examples
- Source: `README.md`
- Commit URL: https://github.com/Scottcjn/Rustchain/blob/5a9d6a8a190008446d4f6c5ed2358bde532ba325/README.md
- Relevant sections: opening project summary; “Every Machine Becomes Vintage”; hardware multiplier table.
- Claims used: Proof-of-Antiquity / DePIN framing; PowerBook G4 2.5x; G5 2.0x; PS3 Cell 2.2x; RISC-V 1.4x; M1 1.2x; modern x86_64 1.0x; modern ARM NAS/SBC 0.0005x.

## S2 — Consensus principle and reward model
- Source: `docs/WHITEPAPER.md`
- Commit URL: https://github.com/Scottcjn/Rustchain/blob/5a9d6a8a190008446d4f6c5ed2358bde532ba325/docs/WHITEPAPER.md
- Relevant sections: §1.3 Core Principles; §3 RIP-200 Round-Robin Consensus; §3.4 Reward Distribution Algorithm.
- Claims used: “1 CPU = 1 Vote”; deterministic round-robin participation; reward weighting by antiquity multiplier; failed fingerprint validation produces zero reward weight in the documented algorithm.

## S3 — Hardware fingerprinting
- Source: `docs/WHITEPAPER.md`
- Commit URL: https://github.com/Scottcjn/Rustchain/blob/5a9d6a8a190008446d4f6c5ed2358bde532ba325/docs/WHITEPAPER.md
- Relevant section: §4 Hardware Fingerprinting System.
- Claims used: six required checks: clock-skew/oscillator drift, cache timing, SIMD identity, thermal drift entropy, instruction path jitter, anti-emulation behavior; ROM fingerprinting for retro platforms.

## S4 — Miner/API flow
- Source: `docs/WHITEPAPER.md`
- Commit URL: https://github.com/Scottcjn/Rustchain/blob/5a9d6a8a190008446d4f6c5ed2358bde532ba325/docs/WHITEPAPER.md
- Relevant sections: §2.2 Node Roles; §2.3 Communication Protocol.
- Claims used: miner clients submit periodic attestations; primary node processes attestations and settles epoch rewards; documented REST endpoints include `/attest/challenge`, `/attest/submit`, `/wallet/balance`, `/epoch`, and `/api/miners`.

## Accuracy boundaries
- No USD/RTC conversion is claimed.
- No live miner count, payout count, profitability, power-use, carbon, benchmark, or token-liquidity claim is used.
- Protocol multipliers are explicitly described as reward-weight multipliers, not compute-speed benchmarks or guaranteed profit.
- Generated visuals are explanatory diagrams. Any terminal frame showing commands is labeled as an example and does not fabricate endpoint output.