# RustChain Payout Ledger Reconciler

Read-only utility for reconciling the public RustChain bounty payout ledger. It parses the canonical Markdown table, totals RTC by status, and flags bookkeeping inconsistencies that matter during adjudication without executing payments or changing any ledger state.

## Checks
- Pending/confirmed entries missing `pending_id`
- Confirmed entries missing `tx_hash`
- Reused pending IDs across different wallet/amount pairs
- Reused transaction hashes across different wallet/amount pairs
- Totals by exact ledger status

## Usage
```bash
python reconcile.py ledger.md --json
python reconcile.py https://raw.githubusercontent.com/Scottcjn/rustchain-bounties/main/path/to/ledger.md --json
python -m unittest discover -s tests -v
```

This prototype is intentionally zero-dependency, read-only, and does not sign, submit, void, confirm, or move RTC.
