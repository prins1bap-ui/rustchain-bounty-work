# Narration script — Queued Is Not Confirmed

A bounty gets approved. Someone writes “queued.” A dashboard adds the number to a total. Five minutes later, everybody is talking as if the money has already arrived.

That shortcut is exactly how payment bookkeeping becomes fiction.

RustChain has a public bounty payout ledger, issue number 104, and it defines four distinct states: **Queued, Pending, Confirmed, and Voided**. Those words are not synonyms. Each one describes a different point in the payout lifecycle.

Start with **Queued**. The ledger defines queued as: approved and transfer submitted. That is meaningful progress. It says the reward has passed approval and entered the transfer process. But the ledger does not define queued as confirmed.

Next is **Pending**. RustChain’s ledger says pending means the transfer is in the network’s 24-hour pending window. The ledger’s active entries show this state with concrete pending IDs and transaction hashes. In other words, pending has evidence attached to it that can be reconciled later.

Then comes **Confirmed**. The published definition is simple: the pending window passed and the transfer confirmed. That is a different evidentiary state from merely being approved or submitted.

And there is a fourth state people tend to forget: **Voided**. Voided means the transfer was canceled before confirmation. The ledger even contains a useful real example. A BoTTube payout for `BoozeLee` was marked voided because of wrong casing, then reissued to `boozelee` under a different pending ID. That one row explains why “a transfer was submitted” and “the transfer ultimately confirmed” should never be collapsed into the same event.

This separation matters because each status answers a different question.

Queued answers: **Has this reward been approved and submitted for transfer?**

Pending answers: **Is there now an identifiable transfer inside the pending window?**

Confirmed answers: **Did that pending transfer make it through the window and confirm?**

Voided answers: **Was it canceled before confirmation?**

RustChain’s own operational notes reinforce that evidence-first approach. The ledger says payout updates should include the bounty reference, wallet, amount, pending ID, and transaction hash. It also says pending confirmations are processed hourly.

That gives anyone reconciling rewards a simple discipline: report the strongest state the evidence actually supports, and no stronger.

If a maintainer says a reward is queued, record it as queued. Do not silently upgrade it to pending without a pending identifier or other authoritative evidence. If a transfer is pending, do not call it confirmed just because the expected confirmation time is approaching. And if a transaction is voided and reissued, keep both events visible instead of pretending the first one never happened.

This is not merely pedantic accounting. It prevents three common mistakes.

First, **double counting**. If queued, pending, and confirmed entries are all added together as though they represent separate rewards, one economic event can appear multiple times.

Second, **premature success claims**. Approval is valuable evidence, but it is not the same evidence as a confirmed transfer.

Third, **lost exceptions**. A void, reissue, corrected wallet, or changed transaction identifier matters precisely because settlement is a process, not a single magical status label.

The clean model is a state transition, not a pile of numbers:

**Queued → Pending → Confirmed**, with **Voided** as a possible exit before confirmation.

And the rule for reporting is even shorter:

**Never promote a payment to a stronger state than the strongest evidence you can point to.**

That is how a public bounty ledger stays useful. Not by making the numbers look bigger, but by making every number mean exactly what it says.

## Runtime

Approximately 650 spoken words. At 135–150 words per minute, target runtime is about 4 minutes 20 seconds to 4 minutes 50 seconds.
