# RustChain bounty #2271 miner dry-run evidence

- Claimant: `@prins1bap-ui`
- RTC wallet: `RTCc5449fe1b93385961152720c864c0f073dae5855`
- Execution environment: GitHub-hosted Ubuntu runner (virtual machine)
- OS: `Linux runnervmgx7h7 6.17.0-1022-azure #22-Ubuntu SMP Mon Jul 27 17:24:03 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux`
- CPU: `AMD EPYC 7763 64-Core Processor`
- Architecture: `x86_64`
- vCPU count: `4`
- Memory: `15Gi`
- Python: `Python 3.12.14`
- RustChain target commit: `5a9d6a8a190008446d4f6c5ed2358bde532ba325`
- Command: `python3 rustchain_linux_miner.py --wallet RTCc5449fe1b93385961152720c864c0f073dae5855 --dry-run --show-payload`
- Exit code: `0`

This was dry-run only. No mining loop, enrollment, transfer, wallet spend, or state-changing action was started.

## Setup note
The first clean-run attempt failed before the dry run because PyNaCl was absent. The repository includes `miners/linux/requirements-miner.txt` with PyNaCl, so the rerun installed that declared miner dependency and repeated the exact dry-run command.

## Output
```text
======================================================================
RustChain Local Linux Miner
RIP-PoA Hardware Fingerprint + Serial Binding v2.0
======================================================================
Node: https://rustchain.org
Wallet: RTCc5449fe1b93385961152720c864c0f073dae5855
Serial: f7f1c74ac1684528
======================================================================

[FINGERPRINT] Running 6 hardware fingerprint checks...
Running 6 Hardware Fingerprint Checks...
==================================================

[1/6] Clock-Skew & Oscillator Drift...
  Result: PASS

[2/6] Cache Timing Fingerprint...
  Result: FAIL

[3/6] SIMD Unit Identity...
  Result: PASS

[4/6] Thermal Drift Entropy...
  Result: PASS

[5/6] Instruction Path Jitter...
  Result: PASS

[6/6] Anti-Emulation Checks...
  Result: FAIL

==================================================
OVERALL RESULT: FAILED
Failed checks: ['cache_timing', 'anti_emulation']
[FINGERPRINT] FAILED checks: ['cache_timing', 'anti_emulation']
[FINGERPRINT] WARNING: May receive reduced/zero rewards

[DRY-RUN] RustChain Linux Miner preflight
[DRY-RUN] No mining or network state will be modified
[DRY-RUN] Node URL: https://rustchain.org
[DRY-RUN] Wallet: RTCc5449fe1b93385961152720c864c0f073dae5855
[DRY-RUN] Hostname: runnervmgx7h7
[DRY-RUN] CPU: AMD EPYC 7763 64-Core Processor
[DRY-RUN] Cores: 4
[DRY-RUN] Memory(GB): 15
[DRY-RUN] MAC count: 1
[DRY-RUN] Serial present: yes
[DRY-RUN] Fingerprint checks available: yes
[DRY-RUN] Fingerprint pass status: False
[DRY-RUN] Health probe: HTTP 200
[DRY-RUN] Node version: 2.2.1-rip200
[DRY-RUN] Response body: {
  "backup_age_hours": 14.685507316854265,
  "db_rw": true,
  "ok": true,
  "tip_age_slots": 0,
  "uptime_s": 353311,
  "version": "2.2.1-rip200"
}
[DRY-RUN] Next real steps would be: attest -> enroll -> mine loop
```
