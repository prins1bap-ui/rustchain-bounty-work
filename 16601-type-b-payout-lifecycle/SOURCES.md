# Source map

## Primary source: RustChain Bounty Payout Ledger

https://github.com/Scottcjn/rustchain-bounties/issues/104

The package relies on the issue’s published status definitions:

- `Queued`: approved and transfer submitted
- `Pending`: in RustChain 24h pending window
- `Confirmed`: pending window passed and transfer confirmed
- `Voided`: canceled before confirmation

The same issue states:

- pending confirmations are processed hourly
- each payout update should include bounty reference, wallet, amount, pending ID, and transaction hash

## Public ledger example: void and reissue

Issue #104 contains two BoTTube ledger rows for the same intended recipient identity:

- wallet `BoozeLee`, Pending ID `27`, status `Voided`, note: wrong casing; reissued to `boozelee`
- wallet `boozelee`, Pending ID `29`, status `Pending`

The script uses this only to demonstrate why a submitted transfer and an ultimately confirmed transfer are not logically identical events. It does not infer the recipient’s current balance or present-day status beyond what the cited ledger row itself says.

## Public confirmed examples

Issue #104 also contains historical rows explicitly labeled `Confirmed`, with pending IDs and transaction hashes. The storyboard may display one of those rows to visually contrast the published Confirmed state with Pending.

## Derived explanatory points

The script’s discussion of double counting, premature success claims, and lost exceptions is analytical explanation derived from maintaining distinct lifecycle states. These are not accusations that RustChain has made those errors.

The state-flow graphic `Queued → Pending → Confirmed`, with `Voided` as a possible pre-confirmation exit, is a visual summary of the four definitions rather than an additional protocol claim.

## Package rules source

RustChain distribution-package bounty #16601:
https://github.com/Scottcjn/rustchain-bounties/issues/16601

This submission is Type B: script + storyboard. It is distinct from the contributor’s Type C reward-drift Shorts package and Type D N64 syndication package; it does not reuse either package’s underlying content.
