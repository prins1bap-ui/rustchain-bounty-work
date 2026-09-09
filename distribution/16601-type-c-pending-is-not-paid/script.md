# Script — target 50–55 seconds

**HOOK (0–6s)**
A crypto bounty says you were paid. Your wallet says the transfer is pending. Which one is true?

**6–17s**
On RustChain, accepted bounty work can enter a two-phase payout: first it is queued, then the transfer sits in a confirmation window.

**17–29s**
That distinction matters. A pending transfer is evidence that payment has been initiated. It is not evidence that the RTC has finally arrived.

**29–41s**
So a clean operator ledger needs separate states: submitted, accepted or queued, pending on-chain, and received. Never promote the last state from a comment, an email, or optimism.

**41–52s**
Verify the wallet or authoritative chain state. Only then count the RTC as received.

**CLOSE (52–56s)**
Pending is progress. Received is money. Keep the two separate.