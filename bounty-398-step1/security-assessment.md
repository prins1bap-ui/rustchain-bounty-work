# RustChain #398 — Step 1 Security Architecture Assessment

Claimant: `@prins1bap-ui`

RTC wallet: `RTCc5449fe1b93385961152720c864c0f073dae5855`

Scope: Step 1 only. This is a defensive architecture assessment. It does not include exploitation, production probing, credential use, fund movement, or attempts to bypass controls.

## 1. Attestation flow

RustChain’s current protocol design makes hardware attestation the core eligibility signal instead of raw hashpower. The documented flow is challenge first, submit second: a miner requests `/attest/challenge`, receives a nonce with an expiry, then sends `/attest/submit` with device metadata and fingerprint evidence. The node validates nonce freshness, rate limits, blocked-wallet state, hardware-binding rules, and fingerprint evidence before the miner is treated as valid for participation.

The important security property is that the server does not simply trust a client-provided statement such as “fingerprint passed.” The protocol documentation explicitly says raw evidence is validated server-side. That matters because the miner is part of the adversarial trust boundary.

Current source also shows that attested state is persisted and reused later. In `node/rustchain_v2_integrated_v2.2.1_rip200.py` around lines 2690–2735, `resolve_enroll_weight_device()` prefers `miner_attest_recent.device_family` and `device_arch`, i.e. device attributes previously stored from attestation, instead of trusting the unsigned `device` object in a later enrollment request. The function comments explain the reason: the enrollment signature covers the miner identity and epoch, not arbitrary device fields, so using the request body directly could let a miner claim a more valuable hardware class than the one actually verified.

That design is sound because the security boundary is moved toward server-derived, previously verified state rather than user-controlled enrollment metadata.

## 2. Hardware fingerprinting and VM-farm resistance

The anti-Sybil model is pragmatic rather than magical. The protocol tries to make cheap identity replication expensive by combining multiple hardware signals, server-side validation, hardware binding, and per-IP controls. The protocol design documentation states that critical fingerprint checks require evidence and that `passed=true` is not trusted by itself. It also describes hardware binding as combining server-observed traits with device traits to reduce the value of spinning up many wallets on one host.

The source reinforces that reward identity is tied to attested hardware. The `resolve_enroll_weight_device()` path is particularly important because reward weighting would otherwise create an economic incentive to lie about architecture. The current code deliberately prefers the verified device stored in `miner_attest_recent`. This turns fingerprinting from a cosmetic gate into an input that directly affects reward eligibility and weighting.

In other words, the VM-farm defense is layered: a fresh attestation must pass, the node keeps verified device state, later enrollment reuses that state, and duplicate/identity controls operate around the same hardware evidence. No single signal needs to be perfect if the combined cost of consistently faking all relevant signals is high enough.

## 3. Epoch reward calculation and distribution

Reward settlement is implemented in `node/rewards_implementation_rip200.py`. Around lines 80–170, `settle_epoch_rip200()` converts slots to epochs, rejects future epochs, opens a database transaction with `BEGIN IMMEDIATE`, checks whether the epoch is already settled, and returns `already_settled` instead of paying twice.

The same function uses RIP-200 time-aged reward calculation and, where available, anti-double-mining logic keyed to hardware identity. The transaction boundary is important because the settled check occurs after acquiring the write lock. That reduces the classic race where two workers both observe “not settled” and both credit the same epoch.

The documented fixed reward pot is 1.5 RTC per epoch in this implementation (`PER_EPOCH_URTC = int(1.5 * UNIT)`). Eligible miners receive proportional shares according to the RIP-200 weighting path. Credits are written to balances, ledger entries are recorded with an epoch-specific reason, epoch reward records are inserted, and the epoch is finally marked settled before commit.

This is a strong auditability pattern: every distribution is associated with an epoch and ledger reason, while settlement is designed to be idempotent.

## 4. Potential attack surface to keep monitoring

The highest-value defensive concern I would keep monitoring is **consistency between verified attestation state and later reward enrollment state**.

The current code already recognizes this class of risk. `resolve_enroll_weight_device()` intentionally avoids trusting unsigned enrollment device data when verified attestation data exists. However, it still contains a compatibility fallback to request-body device data when no stored verified device row is available.

That fallback is understandable for legacy/pre-migration miners, but it creates a trust downgrade: the system moves from server-verified state to caller-supplied state precisely when the expected verified record is missing. I am not asserting that this is currently exploitable, and I did not test it adversarially. From a defensive design perspective, though, this is the place where invariants should be strongest.

A safer long-term policy would be to make the fallback explicitly observable and progressively fail closed as legacy rows disappear. For example, the node could emit a structured audit event whenever enrollment uses unverified fallback device metadata, track the count by epoch, and eventually require fresh attestation before any hardware-weighted reward is granted. That would reduce ambiguity without breaking existing miners abruptly.

## Conclusion

RustChain’s current architecture has the right defensive shape: fresh challenge-response attestations, server-side fingerprint validation, persistence of verified hardware state, reuse of that state for reward weighting, and idempotent transactional epoch settlement. The most important invariant is that reward-relevant attributes should always come from server-verified attestation state rather than unsigned client metadata.

My Step 1 recommendation is therefore not to add more exotic detection logic first, but to keep tightening the boundary between “verified attestation facts” and “compatibility fallbacks.” That is where a relatively small defensive change can preserve the one-physical-machine / one-identity intent of Proof of Antiquity without introducing new complexity.

## Source references

- `Scottcjn/Rustchain` commit `5a9d6a8a190008446d4f6c5ed2358bde532ba325`
- `docs/whitepaper/protocol-design.md`
- `node/rustchain_v2_integrated_v2.2.1_rip200.py`, especially `resolve_enroll_fingerprint()` / `resolve_enroll_weight_device()` around lines 2690–2735
- `node/rewards_implementation_rip200.py`, especially `slot_to_epoch()` / `settle_epoch_rip200()` around lines 80–170
