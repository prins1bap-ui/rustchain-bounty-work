# RustChain #16471 finding: weekly docstring cap trusts the first payout marker from any commenter

Current source: `Scottcjn/rustchain-bounties/scripts/docstring_gate.py`, function `docstring_rtc_this_week()`.

For each `docstring-verified` prior claim, the function fetches up to 100 issue comments, scans them oldest-first, accepts the first `<!-- rtc-payout-amount: N -->` marker it sees, adds that value to weekly earnings, and `break`s. It does not verify the comment author or require the marker to come from the gate.

Concrete wrong-effect path:

1. A claimant posts `<!-- rtc-payout-amount: 0 -->` on their own claim before the gate verifies it.
2. The gate later verifies the claim, adds `docstring-verified`, and posts its authoritative marker, for example `25 RTC`.
3. On a later claim, `docstring_rtc_this_week()` fetches the old claim's comments in chronological order.
4. It sees the claimant's earlier `0` marker first, adds `0`, breaks, and never reads the gate's later `25` marker.
5. `already + amount > MAX_RTC_PER_WEEK` can therefore pass even when the contributor's real verified grants exceed the weekly ceiling. The gate exits normally and can mark the new claim payable.

This is distinct from the payout runner's untrusted *last* marker override: that path changes the amount sent for one claim. This path corrupts the docstring gate's rolling weekly-cap accounting by trusting an untrusted *first* marker on a prior verified claim.

Suggested remediation: accept payout markers only from a trusted gate/maintainer identity, require exactly one authoritative marker, and preferably persist the verified amount in trusted issue state rather than scraping arbitrary public comments.

`repro.py` models the current oldest-first loop and demonstrates that a pre-seeded `0` marker wins over a later authoritative `25` marker.
