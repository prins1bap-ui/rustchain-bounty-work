# Script — Preview the RustChain Miner Install Without Installing It

**Target runtime:** ~40–45 seconds.

**0:00–0:05**
Want to inspect the RustChain miner installer before letting it touch your machine? Use the documented dry-run path.

**0:05–0:15**
The mining guide shows this command:
`curl -sSL https://raw.githubusercontent.com/Scottcjn/Rustchain/main/install-miner.sh | bash -s -- --dry-run`

**0:15–0:27**
A normal install is documented to detect your operating system and CPU, set up Python when needed on Linux, download the miner, create a virtual environment, ask for a wallet name, configure auto-start, and test network connectivity.

**0:27–0:38**
Dry-run is the preview lane. It lets you inspect the installer flow first instead of treating a remote shell command like a magic incantation.

**0:38–0:44**
Read it. Preview it. Then decide whether to install. RustChain gives you the command; you keep the decision.

**On-screen disclosure:** AI-assisted production. Commands and behavior sourced from the public RustChain mining guide.