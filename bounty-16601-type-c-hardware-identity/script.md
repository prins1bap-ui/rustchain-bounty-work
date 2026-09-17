# Short script — One CPU, One Vote

**Target:** 45–55 seconds

Your graphics card is not the point here. RustChain's RIP-200 consensus starts from a different rule: **one CPU equals one vote**.

Instead of rewarding raw hash power, the protocol identifies the physical machine. The miner performs six hardware-level fingerprint checks, then submits that fingerprint with a signed attestation.

Why bother? Because if identity were just a software label, one operator could cheaply multiply virtual machines and pretend they were independent hardware.

Proof-of-Antiquity makes the hardware itself part of the consensus input, then weights valid machines by antiquity.

So the interesting question is not, “How much hash power can I buy?” It is, “What physical computer is actually casting this vote?”

That is RustChain's unusual bet: hardware identity before hash power.
