# rustchain-mcp Operations Guide

This guide is a deployment and troubleshooting companion for `Scottcjn/rustchain-mcp`. It documents only behavior visible in the current public repository and avoids inventing API hosts, credentials, or transport capabilities.

## Install and start

```bash
python -m pip install rustchain-mcp
rustchain-mcp
```

The `rustchain-mcp` process serves MCP over stdio by default. A client launches the process and communicates over its standard input/output streams. Running it does **not** start the separate SSE event relay.

For an MCP client that accepts a command-based server configuration, the essential configuration is:

```json
{
  "mcpServers": {
    "rustchain": {
      "command": "rustchain-mcp"
    }
  }
}
```

## Runtime configuration

The server currently reads these environment variables:

| Variable | Purpose | Repository default |
| --- | --- | --- |
| `RUSTCHAIN_NODE` | Base URL for RustChain node calls | `https://50.28.86.131` |
| `BOTTUBE_URL` | Base URL for BoTTube calls | `https://bottube.ai` |
| `BEACON_URL` | Base URL for Beacon calls | `https://rustchain.org/beacon` |
| `RUSTCHAIN_TIMEOUT` | Request timeout override | server-defined default when omitted |

Example with explicit environment values:

```json
{
  "mcpServers": {
    "rustchain": {
      "command": "rustchain-mcp",
      "env": {
        "RUSTCHAIN_NODE": "https://50.28.86.131",
        "BOTTUBE_URL": "https://bottube.ai",
        "BEACON_URL": "https://rustchain.org/beacon"
      }
    }
  }
}
```

Do not substitute an imagined `api.rustchain.io` host. The repository's server code currently defaults `RUSTCHAIN_NODE` to `https://50.28.86.131`.

## First-run verification

Verify the public RustChain node independently before blaming the MCP client:

```bash
curl -k --fail --max-time 10 https://50.28.86.131/health
```

Then launch the MCP server from a shell:

```bash
rustchain-mcp
```

A healthy stdio MCP server may appear quiet while waiting for an MCP client. Do not diagnose a lack of terminal UI as a startup failure.

After connecting from an MCP client, use read-only tools first:

1. `rustchain_health`
2. `rustchain_epoch`
3. `rustchain_miners`
4. `rustchain_balance` with a known wallet/miner id
5. `bounty_search` for discovery

This sequence separates transport/startup problems from upstream API problems before any wallet-changing operation is attempted.

## MCP event behavior

`rustchain_events` returns a bounded JSON batch. It is not native MCP tool streaming. Progressive consumption is done by calling the tool again with `next_cursor`.

Important response conditions:

- `next_cursor`: pass this value to the next call to continue from the last batch.
- `cursor_expired: true`: the requested older cursor has fallen out of the retained in-memory event window.
- `cursor_reset: true`: the server generation changed, so retained snapshots are replayed safely from the current generation.
- `native_mcp_streaming: false`: the tool is returning bounded batches, not partial tool results.

For non-MCP consumers that need an SSE feed, run the separate relay:

```bash
rustchain-event-relay
curl -N http://127.0.0.1:8766/events
```

The relay is separate from the stdio MCP server. Starting `rustchain-mcp` alone should not be documented as opening port 8766.

## Troubleshooting decision tree

### `rustchain-mcp` is not found

Confirm the Python environment receiving the package is the same environment used by the MCP client:

```bash
python -m pip show rustchain-mcp
python -m pip --version
command -v rustchain-mcp
```

If the package exists but the console script is not on the client's `PATH`, configure the client with the absolute path to the installed `rustchain-mcp` executable rather than changing the server code.

### The MCP client starts the process but reports no tools

Run `rustchain-mcp` directly from a terminal using the same environment. If the process exits immediately, capture that startup error first. If it remains running, inspect the MCP client's stdio launch configuration. The server's default transport is stdio, so pointing a client at an arbitrary HTTP URL is not equivalent.

### RustChain tools fail but BoTTube or Beacon tools work

Check the configured RustChain node:

```bash
curl -k --fail --max-time 10 "${RUSTCHAIN_NODE:-https://50.28.86.131}/health"
```

If that fails, the problem is upstream connectivity or the configured node URL, not MCP tool registration.

### BoTTube tools fail independently

Check the configured BoTTube base URL:

```bash
curl --fail --max-time 10 "${BOTTUBE_URL:-https://bottube.ai}/health"
```

A BoTTube-specific failure should not be treated as proof that RustChain or Beacon tools are unavailable.

### Event consumers receive an expired/reset cursor

Do not fabricate continuity. Respect the response flags and resume from the server-provided retained cursor/generation. Cursor metadata exists precisely so a client can distinguish an ordinary next page from retained-event eviction or relay restart.

## Read-only before write operations

The server includes wallet and transfer capabilities, but troubleshooting should begin with read-only calls. Before using a signed transfer tool, confirm all of the following independently:

- the intended wallet identifier is correct;
- the displayed balance is from the expected node;
- the client is connected to the intended MCP server process;
- any wallet-changing action is explicitly intended by the operator.

This guide intentionally does not provide seed phrases, private keys, or example signatures.

## Tool inventory notes

The README groups tools by service. When updating those lists, keep the stated count synchronized with the actual bullets. In the current README, the BoTTube heading says `5 tools` while seven BoTTube tools are listed (`bottube_stats`, `bottube_search`, `bottube_trending`, `bottube_agent_profile`, `bottube_upload`, `bottube_comment`, `bottube_vote`). The heading should therefore be corrected to `7 tools` unless the underlying exported tool set changes.

## Maintainer verification checklist

Before merging documentation changes that mention runtime behavior:

```bash
# Confirm environment-variable defaults remain true in server.py
grep -nE 'RUSTCHAIN_NODE|BOTTUBE_URL|BEACON_URL|RUSTCHAIN_TIMEOUT' rustchain_mcp/server.py

# Confirm the documented console commands are still packaged
python -m pip show rustchain-mcp

# Confirm README tool counts match their bullet lists
# (manual check is sufficient; no runtime state is changed)
```

The objective is a support document that helps an operator determine whether a problem belongs to package installation, MCP stdio launch, RustChain connectivity, BoTTube connectivity, or event-cursor handling without guessing at nonexistent endpoints or silently changing wallet state.
