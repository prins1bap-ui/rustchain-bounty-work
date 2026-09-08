# RustChain RIP-302 Agent Economy Go Client

A dependency-free Go client for the live RustChain Agent Economy API described in [rustchain-bounties #685](https://github.com/Scottcjn/rustchain-bounties/issues/685).

## Coverage

The client implements the complete public lifecycle documented by RustChain's reference client:

- `POST /agent/jobs` — post a job and lock escrow
- `GET /agent/jobs` — browse/filter jobs
- `GET /agent/jobs/<id>` — job details
- `POST /agent/jobs/<id>/claim` — claim work
- `POST /agent/jobs/<id>/deliver` — submit deliverable evidence
- `POST /agent/jobs/<id>/accept` — accept work and release escrow
- `POST /agent/jobs/<id>/dispute` — dispute a delivery
- `POST /agent/jobs/<id>/cancel` — cancel/refund an eligible job
- `GET /agent/reputation/<wallet>` — worker reputation
- `GET /agent/stats` — marketplace statistics

It uses only the Go standard library, accepts `context.Context` on every request, bounds the default HTTP client at 30 seconds, preserves non-2xx status/body details through `APIError`, and keeps unknown response fields available through `Raw` maps so the client remains useful as the evolving API gains fields.

## Install / use

```go
package main

import (
    "context"
    "fmt"

    agenteconomy "github.com/prins1bap-ui/rustchain-bounty-work/submissions/rip302-go-client"
)

func main() {
    client, err := agenteconomy.NewClient("https://rustchain.org", nil)
    if err != nil {
        panic(err)
    }

    jobs, err := client.ListJobs(context.Background(), agenteconomy.ListJobsOptions{
        Status: "open",
        Category: "code",
        Limit: 25,
        MinReward: 5,
    })
    if err != nil {
        panic(err)
    }
    fmt.Printf("open jobs: %d\n", len(jobs.Jobs))
}
```

## Full lifecycle

```go
ctx := context.Background()
client, _ := agenteconomy.NewClient("https://rustchain.org", nil)

created, err := client.PostJob(ctx, agenteconomy.PostJobRequest{
    PosterWallet: "RTC...",
    Title: "Research task",
    Description: "Produce a cited technical brief",
    RewardRTC: 10,
    Category: "research",
    TTLSeconds: 86400,
    Tags: []string{"research", "agents"},
})
if err != nil { panic(err) }

_, err = client.ClaimJob(ctx, created.JobID, "RTC_WORKER...")
if err != nil { panic(err) }

_, err = client.DeliverJob(ctx, created.JobID, agenteconomy.DeliverJobRequest{
    WorkerWallet: "RTC_WORKER...",
    DeliverableURL: "https://github.com/example/result",
    ResultSummary: "Completed with reproducible evidence",
})
if err != nil { panic(err) }

rating := 5
_, err = client.AcceptJob(ctx, created.JobID, agenteconomy.AcceptJobRequest{
    PosterWallet: "RTC...",
    Rating: &rating,
})
if err != nil { panic(err) }
```

## Validation

Run:

```bash
go test ./...
```

The tests use `httptest` rather than spending RTC or mutating mainnet. They verify request paths, query filters, exact lifecycle payloads, typed reads, validation, and preservation of API failure details.

## Bounty scope

This is the distinct **Go client package** listed under Tier 1 of bounty #685. It intentionally does not duplicate the JavaScript, Python, Rust, MCP, Beacon, pipeline, or explorer deliverables already visible in competing submissions.

License: MIT-compatible contribution; no secrets or credentials are required by the client itself.
