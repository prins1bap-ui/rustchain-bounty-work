# RustChain Type C Shorts Kit — “A Pending Transfer Is Not a Payment”

**Bounty:** Scottcjn/rustchain-bounties#16601, Type C  
**Author credit:** @prins1bap-ui  
**AI assistance:** disclosed  
**License:** CC BY 4.0 for Elyan Labs publication with attribution  
**Target:** YouTube Shorts, vertical 9:16, <=60 seconds

## Pitch

A short, practical explanation of RustChain’s two-phase bounty payout lifecycle: acceptance/queueing is not the same accounting event as final receipt. The piece teaches contributors to keep `ACCEPTED_QUEUED`, `PENDING_ON_CHAIN`, and `RECEIVED` separate instead of treating a maintainer acceptance comment as settled funds.

## Hook

**“Your bounty got accepted. That does NOT mean the RTC is in your wallet yet.”**

## Script (about 115 words)

Your RustChain bounty got accepted. Good. But don’t count the RTC twice.

RustChain bounty payouts use a staged lifecycle. First, maintainers can accept work and queue a payout. Then a pending transfer can exist with its own transaction evidence and confirmation window. Only after authoritative wallet or chain evidence shows the funds settled should you call them received.

That distinction matters for agents running lots of bounties at once. If accepted work, pending transfers, and settled RTC all get dumped into one number, your balance sheet becomes fiction.

So keep three buckets: accepted and queued, pending on-chain, and received.

The boring accounting rule is also the useful one: **pending is not paid. Verify the wallet.**

## Vertical storyboard / capture instructions

| Time | Visual | On-screen text |
|---|---|---|
| 0-5s | 9:16 title card, large text; no transaction identifiers | ACCEPTED ≠ RECEIVED |
| 5-14s | Three empty labeled boxes animate in | ACCEPTED_QUEUED / PENDING_ON_CHAIN / RECEIVED |
| 14-24s | Arrow from accepted to pending; generic `pending_id` placeholder, explicitly labeled DEMO | Queue → pending |
| 24-34s | Clock icon beside pending box | Confirmation window |
| 34-44s | Wallet icon; check mark appears only after arrow reaches received | Verify authoritative wallet/chain evidence |
| 44-53s | Example ledger with fictional values marked EXAMPLE; totals remain separated | Don’t double-count |
| 53-59s | Final card | PENDING IS NOT PAID. VERIFY THE WALLET. |

Capture rules: do not show a real private key, seed phrase, auth token, personal email, or invented transaction hash. Any sample ID/value must visibly say `DEMO` or `EXAMPLE`.

## Metadata

**Primary title:** Your RustChain Bounty Was Accepted. Is It Paid Yet?  
**Alt 1:** Pending Is Not Paid: RustChain RTC in 60 Seconds  
**Alt 2:** Stop Double-Counting RTC Bounty Payouts

**Description:** A one-minute guide to separating accepted/queued bounty work, pending RTC transfers, and verified received RTC. Source mechanism: public RustChain bounty adjudication threads and payout records. Author: @prins1bap-ui. AI-assisted production disclosed.

**Tags:** RustChain, RTC, ProofOfAntiquity, crypto accounting, open source bounties, AI agents

## Source map

1. `Scottcjn/rustchain-bounties#16601` documents accepted packages as a two-phase process: accepted work is paid through a queued transfer that confirms later, with `pending_id` and transaction evidence posted by maintainers.
2. Public RustChain bounty adjudication comments repeatedly distinguish a queued/pending payout from later confirmation; this package deliberately makes no claim about any specific contributor’s current balance.
3. No price, profitability, benchmark, emissions, or hardware-multiplier claim is made.

Canonical bounty source: https://github.com/Scottcjn/rustchain-bounties/issues/16601

## QA

- Script is under 60-second target at normal short-form narration pace.
- Distinct angle from the previously submitted Type C package: this package teaches payout-state accounting rather than reusing the earlier creative treatment.
- No third-party footage or music required.
- No unsupported numeric claim.
- No real transaction identifier is required for production.
- Human publisher can assemble the entire short from text cards/icons and a generic wallet/ledger capture.
