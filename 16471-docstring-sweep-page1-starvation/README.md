# RustChain #16471 finding: scheduled docstring sweep can starve page 2 forever

Current source: `Scottcjn/rustchain-bounties/.github/workflows/docstring-gate.yml`.

The scheduled workflow discovers `awaiting-merge` claims with GitHub Search using `per_page=60`, but it never requests page 2 or reads `total_count`. It then says the rest will process on the next sweep after a separate local 60-attempt cap.

Concrete silent-success path:

1. At least 61 open docstring claims carry `awaiting-merge`.
2. The first 60 remain unmerged across successive sweeps.
3. Every sweep asks only for the first search page (`per_page=60`).
4. Claim 61 is never returned, so it is never rechecked even after its referenced PR becomes merged.
5. Each workflow run can still exit green. The local loop cannot process an item that discovery never returned, and the workflow never reports the omitted search-page count.

This is distinct from the PR-review backfill's 1,000-issue enumeration cap and from PR-review/review-comment pagination findings. It is specifically the scheduled docstring gate's search pagination plus persistent `awaiting-merge` first-page starvation.

Suggested remediation: paginate Search API results until exhaustion (or until a deliberately bounded candidate set is built), use `total_count` to report omitted claims, and preserve a continuation strategy so the same 60 persistent holds cannot monopolize every sweep.

`repro.py` deterministically models 61 persistent awaiting-merge claims. Five consecutive sweeps return the same first 60 and never discover claim 61.
