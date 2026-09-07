# Sources

All technical claims in this package are pinned to RustChain commit:

`be90c9a74d75a975afe2a8a3a1d19eebea3cd0cd`

## Source 1 — Mining guide
https://github.com/Scottcjn/Rustchain/blob/be90c9a74d75a975afe2a8a3a1d19eebea3cd0cd/docs/MINING_GUIDE.md

Supports:
- Proof-of-Antiquity rewards are based on hardware age rather than computational power.
- Each unique hardware device gets one vote per epoch.
- Rewards are adjusted by an antiquity multiplier based on hardware age.
- The six documented fingerprint checks are:
  1. Clock-skew / oscillator drift
  2. Cache timing fingerprint
  3. SIMD unit identity
  4. Thermal drift entropy
  5. Instruction-path jitter
  6. Anti-emulation detection
- The guide states that every miner must prove its hardware is real rather than emulated.

## Source 2 — Protocol overview
https://github.com/Scottcjn/Rustchain/blob/be90c9a74d75a975afe2a8a3a1d19eebea3cd0cd/docs/protocol-overview.md

Supports:
- RustChain documentation describes six fingerprint checks intended to ensure miners run on real physical hardware rather than virtual machines or emulators.

## Claim map
- `script.md` 0:00–0:05: Source 1 hardware-fingerprinting section.
- `script.md` 0:05–0:16: Source 1 six-check list.
- `script.md` 0:16–0:27: Sources 1 and 2 physical-vs-emulated purpose.
- `script.md` 0:27–0:38: Source 1 one-vote-per-epoch and antiquity-multiplier description.
- `script.md` 0:38–0:50: Summary of the cited model; no additional factual claim added.

No benchmark, token-price, profitability, exploit, or deployment claims are made in this package.