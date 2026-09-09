# Sources and claim map

1. **#16601 payout lifecycle** — `accepted → paid (two-phase: queued, confirms ~24h; we post the pending_id + tx)`.
   Source: https://github.com/Scottcjn/rustchain-bounties/issues/16601
   Used for: narration that acceptance can be followed by queued/pending confirmation rather than immediate final receipt.

2. **#16601 Type C definition** — Shorts / clip kit, YouTube Shorts, ≤60s; requires script, vertical-format visuals or exact capture instructions, hook, metadata.
   Source: https://github.com/Scottcjn/rustchain-bounties/issues/16601
   Used for: package format and runtime.

3. **#16497 payout wording** — bounty round describes RTC rewards and evidence requirements; it separately discusses acceptance and later verification for staged content payments.
   Source: https://github.com/Scottcjn/rustchain-bounties/issues/16497
   Used only as corroborating ecosystem context, not for a numerical claim.

## Editorial/inference claims
`Pending is progress. Received is money.` is editorial wording, not a quoted protocol rule. The recommendation to keep SUBMITTED / ACCEPTED_QUEUED / PENDING_ON_CHAIN / RECEIVED separate is an accounting discipline derived from the documented two-phase payout lifecycle, not a claim that RustChain itself names every state exactly that way.