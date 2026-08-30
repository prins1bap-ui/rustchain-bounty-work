# Final narration

**Hook:** This RustChain bounty pays seven RTC. Or ten. It depends which line you read.

Issue thirteen-two-two-six currently says **7 RTC in the title**, while the body says **10 RTC**. That is reward drift: two pieces of the same bounty spec disagree.

So I built a read-only Bounty Spec Linter and Reward Drift Detector. Point it at the issue, and it flags the title-versus-body mismatch instead of making a contributor guess.

It also checks for missing rewards, missing bounty labels, stale open-or-closed wording, and reward differences against `agent.json`.

No payouts are changed automatically. The tool reports the inconsistency so a human can resolve it before bookkeeping turns into archaeology.

**End card:** Make the spec agree before contributors have to guess.

## Timing note

Approximately 113 spoken words before the end card. At 130–145 words per minute, the narration is roughly 47–52 seconds, leaving room for the end card inside a 60-second Short.
