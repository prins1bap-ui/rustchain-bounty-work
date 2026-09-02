# RustChain bounty #2271 miner dry-run evidence

- Claimant: `@prins1bap-ui`
- RTC wallet: `RTCc5449fe1b93385961152720c864c0f073dae5855`
- Execution environment: GitHub-hosted Ubuntu runner (virtual machine)
- OS: `Linux runnervmejwal 6.17.0-1022-azure #22-Ubuntu SMP Mon Jul 27 17:24:03 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux`
- CPU: `AMD EPYC 7763 64-Core Processor`
- Architecture: `x86_64`
- vCPU count: `4`
- Memory: `15Gi`
- Python: `Python 3.12.14`
- RustChain target commit: `5a9d6a8a190008446d4f6c5ed2358bde532ba325`
- Command: `python3 rustchain_linux_miner.py --wallet RTCc5449fe1b93385961152720c864c0f073dae5855 --dry-run --show-payload`
- Exit code: `1`

This was dry-run only. No mining loop, enrollment, transfer, wallet spend, or state-changing action was started.

## Output
```text
Traceback (most recent call last):
  File "/home/runner/work/rustchain-bounty-work/rustchain-bounty-work/target/miners/linux/rustchain_linux_miner.py", line 986, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/rustchain-bounty-work/rustchain-bounty-work/target/miners/linux/rustchain_linux_miner.py", line 967, in main
    miner = LocalMiner(
            ^^^^^^^^^^^
  File "/home/runner/work/rustchain-bounty-work/rustchain-bounty-work/target/miners/linux/rustchain_linux_miner.py", line 271, in __init__
    self.keypair = generate_keypair()
                   ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/rustchain-bounty-work/rustchain-bounty-work/target/miners/linux/miner_crypto.py", line 64, in generate_keypair
    raise RuntimeError("PyNaCl required: pip install PyNaCl")
RuntimeError: PyNaCl required: pip install PyNaCl
```
