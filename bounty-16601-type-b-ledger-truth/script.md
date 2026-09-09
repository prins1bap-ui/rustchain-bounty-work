# Script — Pending Is Not Paid

Estimated runtime: 4–5 minutes at 135–150 words/minute.

## 0:00–0:25 — Hook

A bounty can be accepted. A maintainer can say “paid.” A wallet can even show a transfer record. And you still may not have received the RTC yet.

That sounds pedantic until you try to build an honest earnings tracker. Then one sloppy status label turns into double-counting, fake revenue, and a dashboard that celebrates money that has not settled.

RustChain exposes enough state to avoid that mistake.

## 0:25–1:05 — Three different events

Think of a bounty payout as three separate events.

First, the work is accepted. That is a project decision: the maintainer has approved the contribution.

Second, a payment is queued or enters the pending transfer state. RustChain’s wallet history API exposes lifecycle status rather than forcing clients to guess from a message or an amount.

Third, the transfer becomes confirmed. Only then should a strict accounting system move the amount into a received bucket.

Those events often happen close together, which is exactly why people collapse them into one. They are still different events.

## 1:05–1:50 — Read the wallet, not the wording

The reliable source is the wallet state itself.

RustChain documents `GET /wallet/history` as the wallet-scoped transfer history endpoint. Its transfer records can expose lifecycle state such as `pending` and `confirmed`, along with confirmation-related fields.

That means a tracker does not have to infer settlement from an email saying “paid,” a GitHub comment saying “queued,” or a claim page showing an RTC amount.

Those messages are useful evidence of acceptance. They are not stronger evidence than the chain-facing wallet history for settlement.

The practical rule is simple: human wording tells you what maintainers intend. Wallet history tells you what transfer state actually exists.

## 1:50–2:40 — Why pending deserves its own bucket

A pending transfer is not worthless. It is much stronger than an unreviewed submission. It means the payout process has advanced far enough to create a transfer record.

But it is still not the same thing as confirmed RTC.

A good ledger therefore keeps separate buckets such as submitted, accepted, pending on-chain, and received.

That separation prevents two common errors.

Error one is optimistic accounting: counting every accepted bounty as spendable balance.

Error two is duplicate accounting: counting a queued transfer once when the maintainer announces it and a second time when it finally appears in confirmed wallet history.

If one transfer can only occupy one lifecycle bucket at a time, both errors become much harder to make.

## 2:40–3:30 — A machine-checkable workflow

Here is the clean workflow.

Step one: record the bounty identifier, promised RTC amount, and evidence of acceptance.

Step two: query wallet history for the payout wallet.

Step three: match the transfer using the strongest available identifiers, such as transaction hash, pending identifier, amount plus timestamp, or an idempotency reference when one is available.

Step four: if the wallet record is pending, classify it as pending. Do not silently promote it.

Step five: on a later reconciliation, if that same transfer is confirmed, move it from pending to received exactly once.

And if no matching transfer exists, keep the claim in accepted or queued state rather than inventing settlement.

## 3:30–4:15 — Why this matters beyond bookkeeping

This is not merely an accounting preference.

RustChain’s broader design emphasizes physical verification and machine-checkable evidence. The same philosophy applies to payouts: use the strongest observable state instead of trusting a convenient label.

A truthful earnings system should be able to answer four different questions:

What work did I submit?
What work was accepted?
What transfers are currently pending?
What RTC is actually confirmed in my wallet?

Those totals should not be interchangeable.

## 4:15–4:40 — Close

So when a bounty says “paid,” do not argue with the maintainer and do not blindly trust the word either.

Check the wallet history.

Accepted is a decision. Pending is a transfer in flight. Confirmed is received.

Keeping those states separate makes the numbers boring, accurate, and far more useful. In financial tracking, boring is usually the part that saves you.
