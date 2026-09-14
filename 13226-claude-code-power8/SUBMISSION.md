# Bounty #13226 — Claude Code POWER8 GEO/AEO Package

Claimant: `@prins1bap-ui`

RTC wallet: `RTCc5449fe1b93385961152720c864c0f073dae5855`

Target repository: https://github.com/Scottcjn/claude-code-power8

Bounty: https://github.com/Scottcjn/rustchain-bounties/issues/13226

## Source snapshot

- Upstream branch: `main`
- Upstream commit: `30743d5e9ded94604ebddd426130275254e8fd55`
- README blob used for the patch: `de72bd1298ccc7e64c829c44afb81311fe4a8322`

## Deliverables

1. `llms.txt`
   - answer-first definition
   - canonical links
   - project summary
   - key entities
   - extractable FAQ
   - suggested citation
2. `README.patch`
   - adds one quotable answer-first project definition
   - adds a concise FAQ covering compatibility version, SEA limitation, ppc64le ripgrep, feature scope, and upstream POWER support
   - links the README to the root `llms.txt`

## Collision check

Before implementation:

- Full #13226 comment thread search returned no `claude-code-power8` claim.
- Current target repository code search returned no `llms.txt` file/content.
- Current target repository PR search returned no matching `llms`, `GEO`, or `AEO` PR.

The package is therefore scoped to a repository not already represented in the #13226 claim thread at the time of submission preparation.

## Validation

- Content was checked against the current upstream README rather than inferred from an unrelated RustChain repo.
- Version and architecture statements mirror the target repository's current documented compatibility boundary: Claude Code `2.1.112`, POWER8/ppc64le Linux, Node.js, and ppc64le ripgrep.
- The patch only adds documentation; it does not alter runtime code, dependencies, authentication, network behavior, or payment logic.
- Volatile star counts, bounty counts, token prices, and other unnecessary changing metrics were intentionally omitted from `llms.txt`.
- Canonical repository and upstream links are used rather than invented endpoints.

## Submission route

The connected GitHub App is already known to return `403 Resource not accessible by integration` for upstream issue comments and PR creation. The RustChain bounty submission guide explicitly permits the project email fallback in that condition and states that complete work can be filed upstream on the contributor's behalf. This package is therefore being sent through that documented fallback rather than repeating a known-failing GitHub mutation.

## AI disclosure

This package was produced and validated with ChatGPT acting as the authorized operator for Blake Prins / `@prins1bap-ui`. AI assistance is disclosed explicitly; no test, authorship, hardware, or publication evidence is fabricated.
