# Sources and claim map

All claims were constrained to public RustChain repository material. No payout, price, benchmark, or personal mining-result claim is made.

1. **Protocol overview / Proof of Antiquity / attestation cycle**
   - https://github.com/Scottcjn/Rustchain/blob/main/docs/PROTOCOL_v1.1.md
   - Supports: RustChain describes itself as Proof of Antiquity; RIP-200 context; protocol documentation describes an attestation cycle.

2. **RIP-200 round-robin / 1 CPU = 1 Vote**
   - https://github.com/Scottcjn/Rustchain/blob/main/node/rip_200_round_robin_1cpu1vote.py
   - Supports: RIP-200 round-robin framing and one-CPU/one-vote terminology.

3. **Proof-of-Antiquity fingerprint requirements**
   - https://github.com/Scottcjn/Rustchain/blob/main/specs/RIP_POA_SPEC_v1.0.md
   - Supports: fingerprint payload validation and anti-emulation evidence requirement.

4. **Hardware fingerprint identity description**
   - https://github.com/Scottcjn/Rustchain/blob/main/docs/ISSUE_1449_ANTI_DOUBLE_MINING.md
   - Supports: machines are identified using hardware-fingerprint inputs including architecture and fingerprint profile.

5. **CPU antiquity multiplier documentation**
   - https://github.com/Scottcjn/Rustchain/blob/main/CPU_ANTIQUITY_SYSTEM.md
   - Supports: the project defines antiquity multiplier ranges by hardware generation/class.

6. **Proportional epoch settlement description**
   - https://github.com/Scottcjn/Rustchain/blob/main/campaigns/antiquity_championship/RULES.md
   - Supports: campaign documentation describes standard RIP-200 settlement as one CPU/one vote weighted by antiquity and expresses a miner share as its multiplier relative to the sum of active multipliers.

## Accuracy notes

- Repository documentation has evolved and may contain historical timing or reward parameters. The script therefore avoids asserting a fixed epoch duration or fixed reward pool.
- “One CPU = 1 Vote” is presented as the project’s participation/rotation terminology, not as a claim that every CPU earns an identical amount.
- No claim is made that any particular vintage computer will earn a fixed RTC amount.
