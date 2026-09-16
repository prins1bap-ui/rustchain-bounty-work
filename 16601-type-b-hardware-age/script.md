# The Blockchain That Rewards Hardware for Surviving

**Format:** YouTube explainer
**Target runtime:** ~4:15
**Author credit:** @prins1bap-ui
**Source snapshot:** Scottcjn/Rustchain @ `aa584b344a766f6c0f8613ba7198d1cc7ffbae35`

## 0:00–0:25 — Hook

Most mining systems reward faster or newer hardware. RustChain deliberately experiments with a different rule: hardware age and verifiable physical identity can increase a machine's reward weight. The project calls its consensus design **Proof of Antiquity**.

This is not a promise that an old computer is profitable. It is a look at how the public RustChain design tries to make preservation and physical hardware identity part of consensus.

## 0:25–1:05 — The multiplier idea

RustChain's current README publishes different reward multipliers for hardware classes. At the pinned source snapshot, examples include a PowerPC G4 at 2.5x, a PowerPC G5 at 2.0x, Apple Silicon M1 at 1.2x, and modern x86_64 at 0.8x. The table also assigns higher weights to several much older architectures.

The important point is not any single multiplier. Those values can change. The design choice is that the network does not treat every processor as interchangeable. Hardware class and age are inputs to reward weighting.

## 1:05–1:55 — Why identity matters

That creates an obvious problem: if a miner can simply claim to own old hardware, the incentive collapses.

RustChain therefore describes hardware fingerprinting as part of its Proof-of-Antiquity system. The README lists six categories of checks: clock-skew and oscillator drift, cache timing, SIMD-unit identity, thermal drift entropy, instruction-path jitter, and anti-emulation detection.

The server-side validation description says reported architecture is cross-checked against SIMD features, timing distributions are analyzed, thermal anomalies can be flagged, and repeated ROM hashes can be used to identify suspicious clustering.

Those are project claims about the system's validation design, not a claim that virtualization is mathematically impossible to imitate.

## 1:55–2:40 — What the system is trying to prove

The intended distinction is between a software identity and a physical machine identity.

A normal account can be copied. A VM image can be duplicated. RustChain's design tries to attach participation to characteristics produced by an actual processor and its physical behavior. That is why the project describes itself as a DePIN network for vintage hardware rather than simply another proof-of-work chain.

Its README explicitly contrasts its approach with networks that reward storage, wireless coverage, GPU rendering, or GPU compute. RustChain says its rewarded resource is keeping verified hardware alive.

## 2:40–3:25 — Preservation as an incentive

The unusual economic idea is that age is not automatically a disadvantage. The README describes a system where newer hardware can begin with a lower multiplier and older or rarer classes receive larger weights.

That creates an incentive to keep usable machines operating rather than treating old computers only as obsolete equipment.

But a multiplier is not the same thing as profit. Electricity, maintenance, hardware reliability, token value, network rules, and future multiplier changes all matter. Anyone evaluating mining should verify the current network state rather than extrapolating from a documentation example.

## 3:25–4:05 — Why this is technically interesting

Proof of Antiquity combines two ideas that are normally separate: hardware attestation and an age-weighted reward policy.

The attestation side asks, in effect, "What physical machine is participating?" The reward side then asks, "How should that verified hardware class be weighted?"

Whether that model succeeds at scale is an empirical question. But it creates a testable architecture: published hardware classes, measurable fingerprint signals, server-side validation, and observable network participation.

## 4:05–4:20 — Close

If you want to inspect the implementation rather than take a narration at face value, start with the RustChain repository and its Proof-of-Antiquity documentation. This package's `SOURCES.md` pins every technical statement here to the exact public source snapshot used during production.
