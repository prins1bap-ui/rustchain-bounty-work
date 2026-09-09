# Sources / Claim Map

Canonical public source reviewed for this package:

- RustChain README: https://github.com/Scottcjn/Rustchain/blob/main/README.md

## Claim map

1. **RustChain describes its consensus as Proof of Antiquity and frames it as one CPU = one vote.**
   - Source: RustChain README, `PROOF OF ANTIQUITY` and `PROOF OF ANTIQUITY CONSENSUS` sections.

2. **Generic ARM / RPi / Phones base multiplier is 0.0005×.**
   - Source: RustChain README, `TENURE-GROWN MULTIPLIERS (RIP-200)` table, row `Generic ARM / RPi / Phones`.

3. **The project's stated reason for generic ARM's near-zero weight is that cheap ARM boards and broken phones enable trivial fleet/51% attacks.**
   - Source: RustChain README, `WHY IS GENERIC ARM NEAR ZERO?` explanatory block.

4. **Apple Silicon M1/M2/M3 is listed separately at 1.20×.**
   - Source: RustChain README, `TENURE-GROWN MULTIPLIERS (RIP-200)` table, row `Apple Silicon (M1/M2/M3)`.

5. **The README says Apple Silicon gets 1.2× because its Secure Enclave makes hardware fingerprinting reliable and spoofing expensive.**
   - Source: RustChain README, `WHY IS GENERIC ARM NEAR ZERO?` explanatory block.

## Accuracy boundary
The short reports the project's published rules and stated rationale. It does not independently validate that the fingerprint system defeats all spoofing, that the multiplier policy is economically optimal, or that any device will earn a particular amount of RTC.
