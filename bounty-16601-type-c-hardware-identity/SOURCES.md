# Sources and claim map

Pinned source revision used for verification: `Scottcjn/Rustchain@aa584b344a766f6c0f8613ba7198d1cc7ffbae35`.

## Claim: RIP-200 uses “1 CPU = 1 Vote” and replaces hash power with hardware identity
Source: `docs/PROTOCOL_v1.1.md`, §2 Consensus: RIP-200 (Proof-of-Antiquity).
https://github.com/Scottcjn/Rustchain/blob/aa584b344a766f6c0f8613ba7198d1cc7ffbae35/docs/PROTOCOL_v1.1.md

## Claim: miner performs six hardware-level checks and submits the fingerprint with a signed payload
Source: `docs/PROTOCOL_v1.1.md`, consensus flow immediately following §2.
https://github.com/Scottcjn/Rustchain/blob/aa584b344a766f6c0f8613ba7198d1cc7ffbae35/docs/PROTOCOL_v1.1.md

## Claim: Proof-of-Antiquity is designed around physical hardware identity and discounts/rejects virtualized environments that can cheaply scale
Source: `docs/whitepaper/hardware-fingerprinting.md`.
https://github.com/Scottcjn/Rustchain/blob/aa584b344a766f6c0f8613ba7198d1cc7ffbae35/docs/whitepaper/hardware-fingerprinting.md

## Claim: antiquity multipliers are used for rewards
Source: `node/rip_200_round_robin_1cpu1vote.py` module documentation: deterministic round-robin producer selection and time-aging antiquity multipliers for rewards.
https://github.com/Scottcjn/Rustchain/blob/aa584b344a766f6c0f8613ba7198d1cc7ffbae35/node/rip_200_round_robin_1cpu1vote.py

## Accuracy boundaries
This package intentionally avoids specific multiplier values, profitability claims, token-price claims, guaranteed VM-detection claims, benchmarks, or statements that a particular machine will earn a particular amount. The short explains the documented design and protocol flow only.
