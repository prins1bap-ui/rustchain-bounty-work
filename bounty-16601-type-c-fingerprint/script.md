# Script — Six Signals, One Physical Miner

**Target runtime:** ~50–55 seconds at a natural 125–135 wpm pace.

**0:00–0:05**
Hook: RustChain does not just ask what CPU you claim to have. It asks the hardware to prove itself.

**0:05–0:16**
Its mining guide documents six fingerprint signals: clock and oscillator drift, cache timing, SIMD identity, thermal drift entropy, instruction-path jitter, and anti-emulation detection.

**0:16–0:27**
Those checks are meant to distinguish real physical machines from virtualized or emulated ones by looking at behavior tied to the underlying silicon and microarchitecture.

**0:27–0:38**
That matters because Proof-of-Antiquity is not a raw-speed contest. The guide says each unique hardware device gets one vote per epoch, then rewards are adjusted by an antiquity multiplier tied to hardware age.

**0:38–0:50**
So the idea is simple: prove the machine is physically real, identify what it is, then reward age rather than benchmark dominance. Six signals. One physical miner. Proof-of-Antiquity.

**On-screen disclosure:** Created with AI assistance; technical claims sourced from the public RustChain repository.