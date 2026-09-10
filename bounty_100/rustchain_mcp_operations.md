# RustChain MCP Operations Quickstart

This operator-focused guide turns the public `Scottcjn/rustchain-mcp` interface into a short, reproducible setup and troubleshooting path for MCP clients.

## Install and launch

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install rustchain-mcp
rustchain-mcp
```

The console script serves MCP over stdio by default. A client should launch the process itself rather than expecting a web listener.

## Client configuration

A minimal MCP client configuration is:

```json
{
  "mcpServers": {
    "rustchain": {
      "command": "rustchain-mcp"
    }
  }
}
```

Restart the MCP client after changing its configuration so it can spawn the server and enumerate tools.

## Configuration knobs

The server reads these optional environment variables:

| Variable | Purpose |
| --- | --- |
| `RUSTCHAIN_NODE` | Override the primary RustChain node URL |
| `BOTTUBE_URL` | Override the BoTTube service URL |
| `BEACON_URL` | Override the Beacon service URL |
| `RUSTCHAIN_TIMEOUT` | Bound upstream HTTP requests |

Example:

```bash
RUSTCHAIN_TIMEOUT=15 rustchain-mcp
```

Avoid putting wallet seed phrases or private keys in MCP configuration files. Wallet secrets belong in the package's encrypted local keystore, not in tool arguments or environment examples.

## Read-only smoke test

After the MCP client connects, verify the integration without spending RTC or changing remote state:

1. Call `rustchain_health` and confirm a structured response is returned.
2. Call `rustchain_epoch` and confirm epoch data is returned.
3. Call `bounty_search` with a narrow keyword and confirm a bounded result set.
4. Optionally call `network_health` to compare the configured RustChain nodes.

These checks establish that the process launched, MCP tool discovery worked, and upstream reads are reachable. They deliberately avoid wallet creation, transfers, uploads, comments, votes, and Beacon messages.

## Event consumers

`rustchain_events` returns bounded JSON batches. It is not native MCP streaming. Continue with the returned `next_cursor` when progressive results are needed.

For non-MCP consumers that specifically need SSE, run the separate relay:

```bash
rustchain-event-relay
curl -N http://127.0.0.1:8766/events
```

The relay is separate from the stdio MCP server and should remain loopback-only unless an operator intentionally adds an authenticated network boundary.

## Failure triage

### Client shows no RustChain tools

Run `rustchain-mcp` in a terminal first. If the process cannot start, fix the local installation before debugging the MCP client. If it starts normally, re-check that the client command is exactly `rustchain-mcp` and restart the client.

### Read tools return upstream errors

Check `rustchain_health` first. If only one upstream service is affected, verify the corresponding `RUSTCHAIN_NODE`, `BOTTUBE_URL`, or `BEACON_URL` override. Do not interpret a failed lookup as a zero balance or empty result.

### Calls time out

Set a bounded `RUSTCHAIN_TIMEOUT` and retry a read-only health call. A timeout is an availability result, not evidence that the requested wallet, bounty, video, or agent does not exist.

### Need continuous events

Do not repeatedly relaunch the MCP server expecting HTTP streaming. Use cursor-based `rustchain_events` calls from MCP, or the separate `rustchain-event-relay` for SSE consumers.

## Operator acceptance checklist

- `rustchain-mcp` launches successfully over stdio.
- The client enumerates RustChain MCP tools.
- `rustchain_health` returns structured data.
- `rustchain_epoch` returns structured data.
- A bounded `bounty_search` succeeds.
- No secret is pasted into configuration or logs.
- No RTC transfer or other state-changing call is needed for the smoke test.

## Sources

This guide is derived from the public `Scottcjn/rustchain-mcp` README and server configuration. It intentionally documents only operator-visible behavior already exposed by the project and does not claim unverified endpoints or credentials.