# What Actually Happens in a RustChain Epoch?

**Format:** 3–4 minute narrated explainer
**Author credit:** @prins1bap-ui
**AI disclosure:** Drafted with ChatGPT assistance and source-checked against the public RustChain repository.

## 0:00–0:25 — Hook

Most blockchains make the competition about hash power or capital. RustChain experiments with a different question: can a network make physical computer identity and hardware age part of how participation is weighted?

That experiment is called Proof of Antiquity. Its RIP-200 implementation describes a round-robin model summarized as “1 CPU = 1 Vote,” then applies hardware-age weighting when rewards are distributed.

## 0:25–1:05 — First, the machine has to attest

A miner does not simply announce that it owns old hardware and collect a larger share. RustChain’s protocol documentation describes an attestation cycle in which a miner submits hardware information and fingerprint evidence. The Proof-of-Antiquity specification requires fingerprint data and specifically requires anti-emulation evidence.

The important idea is that the protocol is trying to bind participation to observable properties of a physical machine rather than treating every software process as an independent voter.

## 1:05–1:45 — One CPU, one turn

RIP-200’s round-robin code states the rule directly: each attested CPU gets one turn per rotation cycle. That is deliberately different from a lottery where a faster machine can buy more chances simply by hashing faster.

The “vote” here should not be confused with a political vote or a promise of equal earnings. It describes participation in the rotation. Reward weighting is a separate step.

## 1:45–2:30 — Antiquity changes the weight

RustChain then applies an antiquity multiplier. The project’s CPU antiquity documentation defines multiplier ranges for hardware generations, while the live RIP-200 code is the source to consult for the actual implementation.

That distinction matters: “one CPU = one vote” does not mean every CPU receives the same reward. A machine can have one participation slot while its verified hardware class or age changes its reward weight.

This is the unusual part of the design. In most compute systems, newer and faster hardware is the obvious advantage. Proof of Antiquity intentionally gives older verified hardware a reason to remain economically relevant inside this experimental network.

## 2:30–3:10 — Settlement is proportional, not magical

The project’s own campaign documentation gives the settlement relationship in plain language: a miner’s share is its multiplier divided by the sum of active multipliers. That means the result depends on who else is active in the epoch and how those machines are weighted.

So there is no honest way to say that a particular old computer is guaranteed to earn a fixed amount. The protocol can define relative weighting; actual settlement depends on the active set and the network’s current reward rules.

## 3:10–3:35 — Takeaway

The clean mental model is three steps: attest the physical machine, give each accepted CPU its place in the rotation, then apply the protocol’s antiquity weighting during reward distribution.

Whether that experiment succeeds is an empirical question. But mechanically, that is what makes RustChain different: it tries to turn hardware identity and computing history into protocol inputs instead of treating old machines as electronic furniture.

Repository: https://github.com/Scottcjn/Rustchain
