# RustChain: Why a 2003 PowerBook Can Outrank Modern Hardware

**Target runtime:** 4–6 minutes  
**Source lock:** `Scottcjn/Rustchain@5a9d6a8a190008446d4f6c5ed2358bde532ba325`  
**Author credit:** @prins1bap-ui  
**Bounty:** #16601 Type A full production kit

## 00:00–00:35 — Hook

Most cryptocurrency mining rewards one thing: more compute. Faster chips, larger farms, newer hardware. RustChain deliberately flips that incentive. Its Proof-of-Antiquity design gives verified older hardware higher reward weight than the modern baseline. The project’s current README gives a concrete example: a PowerBook G4 from 2003 is listed at a 2.5-times antiquity multiplier, while modern x86-64 is the 1.0-times baseline. The point is not that the G4 is faster. It plainly is not. The point is that preserving authentic old hardware is the resource RustChain is trying to reward.

## 00:35–01:20 — One CPU, one vote

The whitepaper describes the core consensus principle as “one CPU equals one vote.” RustChain’s RIP-200 round-robin design gives validated hardware devices block-production turns rather than letting raw hash power buy more votes. Reward distribution is then weighted by an antiquity multiplier. In the whitepaper’s model, a miner that fails hardware fingerprint validation receives zero weight for that reward calculation. That separation matters: identity and authenticity determine whether the hardware is admitted, while the antiquity tier determines its reward weight.

This is a very different optimization target from conventional proof-of-work. Buying ten times more modern compute is not supposed to create ten times more identity for one physical machine.

## 01:20–02:20 — Six hardware checks

So how does the network distinguish an actual old machine from a virtual machine claiming to be one? The current RustChain whitepaper documents six required hardware-fingerprint checks, with a seventh ROM check on retro platforms.

First is clock-skew and oscillator drift, looking for timing behavior from physical silicon. Second is cache timing, measuring characteristics of the memory hierarchy. Third is SIMD unit identity, which helps cross-check the claimed architecture against instruction behavior such as AltiVec, SSE, or NEON. Fourth is thermal-drift entropy. Fifth is instruction-path jitter, another timing signature of a real microarchitecture. Sixth is anti-emulation behavioral detection. Retro platforms can add ROM fingerprinting to identify known emulator ROMs or suspicious clustering.

The important idea is cross-validation. A miner is not supposed to earn a vintage bonus merely because a payload says “PowerPC G4.” The network is designed to compare multiple physical signals against the claimed machine.

## 02:20–03:10 — The multiplier table

The README shows how strongly the design favors hardware diversity. PowerPC G4 is listed at 2.5 times. PowerPC G5 is 2.0 times. A PS3 Cell Broadband Engine is 2.2 times. RISC-V is 1.4 times. Apple Silicon M1 is 1.2 times. Modern x86-64 is the 1.0 baseline. At the other end, modern ARM NAS and single-board-computer hardware is shown at a 0.0005-times penalty tier because cheap, easily farmed devices are not the scarcity the protocol is trying to preserve.

These figures are protocol multipliers, not speed benchmarks and not guaranteed profit. Actual rewards depend on the network’s reward process and the set of validated miners. This package deliberately does not convert those multipliers into dollar earnings.

## 03:10–04:00 — What a miner actually does

The whitepaper describes a straightforward REST flow. A miner requests an attestation challenge, submits hardware attestation data, and can query endpoints for wallet balance, epoch information, and active miners. The primary node validates hardware fingerprints and participates in epoch settlement. Miner clients periodically submit hardware proof and receive rewards according to the protocol rules.

That means the “mining” story is really an identity-and-attestation story. The machine is proving what it is, not racing to perform pointless hashes faster than everybody else.

## 04:00–04:45 — Why this is interesting

Whether Proof-of-Antiquity becomes a durable economic system is an empirical question, not something a video should pretend is already settled. What is technically interesting is the incentive experiment: can a blockchain make hardware age and authenticity economically relevant instead of treating older machines as obsolete waste?

RustChain’s answer is to combine deterministic participation, hardware fingerprinting, and explicit antiquity multipliers. A PowerBook G4 does not beat a Threadripper at compute. Under this protocol, it can outrank it on the dimension RustChain chose to reward: authenticated age and preservation.

## 04:45–05:05 — Close

If you want to inspect the mechanism rather than take a narrator’s word for it, start with the RustChain README and technical whitepaper on GitHub. The source links for every factual claim in this video are included with this production kit. Old hardware still computes. RustChain is an experiment in making that survival count.