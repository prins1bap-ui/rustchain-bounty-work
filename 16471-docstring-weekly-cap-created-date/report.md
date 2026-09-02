# #16471 finding — docstring weekly cap counts issue age, not verification age

## Current source

`Scottcjn/rustchain-bounties/scripts/docstring_gate.py`

The gate says `docstring_rtc_this_week(author)` computes RTC the author has **already been granted for docstrings in 7 days**. But candidate discovery is filtered with:

```python
since = (now_utc - timedelta(days=7)).strftime("%Y-%m-%d")
q = (
    f"repo:{REPO} is:issue author:{author} label:docstring-verified "
    f"created:>{since}"
)
```

The payout marker being summed lives in a gate **comment**. Therefore an issue opened more than seven days ago but adjudicated/verified during the current seven-day window is omitted before its payout marker is examined.

## Silent-success path

1. Contributor opens docstring claim A more than seven days ago.
2. Its PR merges late and the gate verifies A today, adding `docstring-verified` and a trusted `rtc-payout-amount` marker.
3. Contributor has a new claim B adjudicated today.
4. `docstring_rtc_this_week()` searches only issues with `created:>{since}`.
5. A is absent because the **claim issue creation date** is old, even though its verified award is current.
6. The function returns an understated `already` total.
7. B can pass `already + amount <= MAX_RTC_PER_WEEK`, receive `bounty-eligible`, and the workflow exits normally.

No command fails and no warning identifies that recent verified RTC was omitted. The rolling weekly ceiling can therefore be exceeded silently.

## Why this is distinct

This is not the previously reported failure-open path where the GitHub earnings lookup itself errors. Here GitHub returns successful, valid data; the query asks for the wrong time dimension. It is also distinct from the earlier `awaiting-merge` retry/dead-end report: this finding concerns the correctness of the weekly earnings sum after successful verification.

## Deterministic reproduction

See `poc.py`. It models a claim created eight days ago but verified one day ago. A creation-date filter excludes it even though a verification-date rolling window must include it.

## Suggested fix

Do not use issue `created_at` to define weekly earnings. Enumerate the contributor's `docstring-verified` claims (with pagination) and inspect the timestamp of the trusted gate comment carrying `rtc-payout-amount`, summing markers whose trusted comment `created_at` falls inside the rolling seven-day window. Alternatively persist an authoritative verification/payout timestamp and query that directly.
