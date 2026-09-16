# SOURCES — claim-by-claim verification

All RustChain claims in this package were checked against:

- Repository: `Scottcjn/Rustchain`
- Commit: `aa584b344a766f6c0f8613ba7198d1cc7ffbae35`
- Pinned README: https://github.com/Scottcjn/Rustchain/blob/aa584b344a766f6c0f8613ba7198d1cc7ffbae35/README.md
- Whitepaper entry point: https://github.com/Scottcjn/Rustchain/blob/aa584b344a766f6c0f8613ba7198d1cc7ffbae35/docs/WHITEPAPER.md

| Script claim | Source |
|---|---|
| RustChain describes its consensus design as Proof of Antiquity. | Pinned `README.md`, project header / Proof of Antiquity badge and introductory sections. |
| Current documentation assigns different multipliers to hardware classes. | Pinned `README.md`, `Why This Exists` hardware multiplier table. |
| Examples at this snapshot: PowerPC G4 2.5x, PowerPC G5 2.0x, Apple Silicon M1 1.2x, modern x86_64 0.8x. | Pinned `README.md`, introductory G4/G5 statements and `Why This Exists` multiplier table. |
| Hardware fingerprinting is part of the project's validation design. | Pinned `README.md`, `AI-Augmented Consensus` → `Hardware Fingerprinting`. |
| Six listed categories are oscillator drift, cache timing, SIMD identity, thermal entropy, instruction jitter, and anti-emulation detection. | Pinned `README.md`, `Hardware Fingerprinting (6 Checks...)` block. |
| Server-side validation cross-checks SIMD/architecture, analyzes timing distributions, flags thermal anomalies, and detects ROM clustering. | Pinned `README.md`, `Server-Side AI Validation` bullets. |
| RustChain frames itself as a DePIN for vintage hardware. | Pinned `README.md`, header and `How RustChain Compares to DePIN Leaders`. |
| The comparison table distinguishes RustChain's physical-infrastructure/reward model from coverage, storage, rendering and GPU-compute networks. | Pinned `README.md`, `How RustChain Compares to DePIN Leaders` table. |
| The project explicitly presents hardware longevity/preservation as an incentive. | Pinned `README.md`, `Every Machine Becomes Vintage` and `Why This Exists`. |

## Accuracy decisions

This package deliberately does **not** repeat several stronger promotional formulations as established facts. In particular:

- It does not promise mining profitability.
- It does not claim fingerprinting is mathematically impossible to spoof.
- It does not present projected future multipliers as guaranteed network policy.
- It does not use the README's external market-size, developer-loss, funding, emissions, or e-waste figures because those would require independent source verification beyond the repository.
- It describes hardware-fingerprinting behavior as the project's documented design rather than independently validated security guarantees.

This narrower wording is intentional so the package remains technically defensible under bounty #16601's factual-accuracy requirement.
