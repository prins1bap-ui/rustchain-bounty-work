# RustChain RIP-302 Agent Economy Rust Client

A focused Rust client crate for the Agent Economy API documented by `Scottcjn/rustchain-bounties#685`.

## Bounty target

The current issue is open and lists **Tier 1: SDK/Client Library — 50 RTC each**, including a **Rust client crate**.

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

The default base URL is the primary node URL stated in #685: `https://50.28.86.131`.

## Deliberate anti-hallucination behavior

The issue documents exact request examples for posting, claiming, and delivering, so those have typed request structures. The issue lists the accept/dispute/cancel routes but does **not** document their request bodies. For those methods the crate accepts an explicit caller-provided JSON object instead of inventing field names.

Successful responses are returned as `serde_json::Value` because #685 does not publish a stable response schema for every route. Non-success HTTP bodies are preserved in errors for diagnostics.

## Safety and verification boundary

This submission does **not** perform any live mutating Agent Economy request. No live job was posted or claimed, no escrow was funded, and no RTC was signed, transferred, released, refunded, tipped, bridged, or otherwise moved.

All mutating route tests use a local mock HTTP server. The SDK contains those methods because they are part of the documented API contract, not because this bounty submission exercised financial state changes.

## Read-only example

```rust,no_run
use rustchain_agent_economy::AgentEconomyClient;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = AgentEconomyClient::default_node()?;
    let jobs = client.browse_jobs().await?;
    println!("{jobs:#}");
    Ok(())
}
```

## QA

The repository CI runs these commands from this directory:

```text
cargo fmt --all -- --check
cargo test --all-targets
cargo clippy --all-targets --all-features -- -D warnings
```

The ChatGPT execution environment used to prepare this submission did not contain a local Rust toolchain, so no local `cargo` pass is claimed. GitHub Actions is used as the independent Rust build/test environment. That distinction is intentional rather than pretending a compiler existed where it did not.

## Attribution

Prepared by an AI agent for GitHub user `@prins1bap-ui` with the operator's authorization. No maintainer acceptance or payout is implied by publication of this code.
