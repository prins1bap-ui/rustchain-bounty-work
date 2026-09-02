# RustChain RIP-302 Agent Economy Rust Client

A focused Rust client crate for the Agent Economy API targeted by `Scottcjn/rustchain-bounties#685` and reconciled against the current public `Scottcjn/Rustchain` RIP-302 implementation.

## Bounty target

The current issue remains open and lists **Tier 1: SDK/Client Library — 50 RTC each**, including a **Rust client crate**.

## Implemented routes

- `POST /agent/jobs`
- `GET /agent/jobs`
- `GET /agent/jobs/<id>`
- `POST /agent/jobs/<id>/claim`
- `POST /agent/jobs/<id>/deliver`
- `POST /agent/jobs/<id>/accept`
- `POST /agent/jobs/<id>/dispute`
- `POST /agent/jobs/<id>/cancel`
- `GET /agent/reputation/<wallet>`
- `GET /agent/stats`

The default base URL remains the primary node URL stated in #685: `https://50.28.86.131`.

## Current-main contract coverage

The crate now models the public RIP-302 implementation rather than relying only on the older abbreviated bounty examples:

- posting requires a wallet, title, description, category, and bounded RTC reward; optional TTL and tags are supported
- job browsing has a typed `BrowseJobsQuery` for category, status, limit, offset, and minimum reward, plus a raw-query escape hatch for forward compatibility
- delivery supports the server's `deliverable_url` **or** `result_summary` rule and optional `deliverable_hash`
- accept, dispute, and cancel use typed request structures matching current public server fields
- obvious invalid inputs fail before any network request
- non-success response bodies are preserved for diagnostics

Successful responses intentionally remain `serde_json::Value` because the public API does not publish a stable Rust response schema for every route and may add fields over time.

## Safety and verification boundary

This submission does **not** perform live mutating Agent Economy requests. No live job is posted, claimed, accepted, cancelled, disputed, or funded during tests. No RTC is signed, transferred, released, refunded, tipped, bridged, or otherwise moved.

All mutation-route tests use a local mock HTTP server. The SDK exposes the documented client surface without exercising live financial state changes.

## Read-only example

```rust,no_run
use rustchain_agent_economy::{AgentEconomyClient, BrowseJobsQuery};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = AgentEconomyClient::default_node()?;
    let jobs = client
        .browse_jobs_filtered(&BrowseJobsQuery {
            category: Some("code".into()),
            min_reward: Some(10.0),
            ..BrowseJobsQuery::default()
        })
        .await?;
    println!("{jobs:#}");
    Ok(())
}
```

## QA

Repository CI runs from this crate directory:

```text
cargo fmt --all -- --check
cargo test --all-targets
cargo clippy --all-targets --all-features -- -D warnings
```

The current-contract regression suite checks typed browse filters, post/claim/deliver payloads, accept/dispute/cancel payloads, input validation, route safety, and preservation of non-success response bodies.

## Attribution

Prepared and maintained for GitHub user `@prins1bap-ui` with AI assistance under operator authorization. No maintainer acceptance or payout is implied by publication of this code.
