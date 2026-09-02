# RustChain dry-run before mining — <=60s short

**Hook:** Before you let a RustChain miner touch the network, make it show its homework.

**Narration (~42 seconds):**

RustChain's Linux miner docs give you a simple preflight step: run the miner with `--dry-run --show-payload` before live operation. That lets you inspect what the miner intends to send without pretending a live submission already happened.

From the RustChain repo, enter the Linux miner directory, prepare the documented Python environment, then run:

`python3 rustchain_linux_miner.py --dry-run --show-payload`

The point is verification before trust: inspect the generated payload, confirm the command behaves as expected on your machine, and only then decide whether to run live.

The exact command is documented in RustChain's current miner setup guide. Source link is in the description.

**End card:** Inspect first. Run live second.
