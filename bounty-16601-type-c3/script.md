# Script — Why Does RustChain Nearly Zero Out Generic ARM?

**Target:** 50–58 seconds at a natural 135–150 wpm.

**0:00–0:05 — Hook**
Why would a blockchain welcome old computers, then give a Raspberry Pi almost no reward weight?

**0:05–0:15**
RustChain calls its model Proof of Antiquity. Its published multiplier table gives generic ARM devices a base weight of just **0.0005×**.

**0:15–0:28**
The reason in the project documentation is anti-flood economics: cheap ARM boards and broken phones are easy to accumulate in large numbers, so a low weight makes a pile of inexpensive devices a poor shortcut to network influence.

**0:28–0:39**
That is different from Apple Silicon. RustChain lists Apple M1, M2, and M3 systems separately at **1.20×**, citing their Secure Enclave as making hardware fingerprinting more reliable and spoofing more expensive.

**0:39–0:51**
So the rule is not simply “old hardware good, ARM bad.” The network is trying to price the cost of multiplying physical identities while still rewarding hardware it believes it can fingerprint reliably.

**0:51–0:57 — Close**
That tradeoff is one of the stranger, and more interesting, parts of RustChain’s one-CPU-one-vote experiment.
