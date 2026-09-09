# Sources and Claim Map

All factual claims in this package are grounded in public RustChain repository material. No private emails, private wallet data, or invented performance/economic claims are used.

## S1 — RustChain is a DePIN / Proof-of-Antiquity network with hardware verification
Source: `Scottcjn/Rustchain/README.md`
https://github.com/Scottcjn/Rustchain/blob/main/README.md

Supports the framing that RustChain emphasizes machine-checkable physical verification and hardware fingerprinting.

## S2 — Wallet history exposes transfer lifecycle state
Source: `docs/WALLET_TRANSFER_STATE_GUIDE.md`
https://github.com/Scottcjn/Rustchain/blob/main/docs/WALLET_TRANSFER_STATE_GUIDE.md

Relevant documented concept: `GET /wallet/history` returns wallet-scoped transfer records and documents lifecycle statuses including `pending` and `confirmed`.

## S3 — Public wallet-history endpoint and fields
Source: `docs/API.md`
https://github.com/Scottcjn/Rustchain/blob/main/docs/API.md

Supports the use of the public wallet-history API as a read-only settlement-state source.

## S4 — Signed transfers use a pending/confirmation lifecycle
Source: `docs/API_REFERENCE.md`
https://github.com/Scottcjn/Rustchain/blob/main/docs/API_REFERENCE.md

Supports the statement that signed transfer workflows distinguish transfer submission/pending state from later confirmation.

## S5 — Wallet transfer and pending confirmation paths are treated as explicit protocol/security surfaces
Source: `SECURITY.md`
https://github.com/Scottcjn/Rustchain/blob/main/SECURITY.md

Supports the statement that wallet transfer and pending-confirmation paths are distinct enough to be reviewed and tested directly.

## Claim discipline
The script deliberately does **not** claim:
- that every maintainer message uses identical terminology;
- that a pending transfer is guaranteed to confirm;
- that a specific confirmation delay always applies;
- that any private user balance or payout is representative of the network;
- that RTC has any guaranteed monetary value.

The accounting recommendation — keep submitted, accepted, pending, and received separate — is an implementation discipline derived from the documented lifecycle states rather than a claim that RustChain mandates those exact internal bucket names.
