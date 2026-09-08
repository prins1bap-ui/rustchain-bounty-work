package agenteconomy

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
)

func testClient(t *testing.T, handler http.HandlerFunc) (*Client, *httptest.Server) {
	t.Helper()
	ts := httptest.NewServer(handler)
	c, err := NewClient(ts.URL, ts.Client())
	if err != nil { t.Fatalf("NewClient: %v", err) }
	return c, ts
}

func decodeBody(t *testing.T, r *http.Request, dst any) {
	t.Helper()
	if err := json.NewDecoder(r.Body).Decode(dst); err != nil { t.Fatalf("decode body: %v", err) }
}

func TestLifecyclePayloads(t *testing.T) {
	seen := map[string]bool{}
	c, ts := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		switch {
		case r.Method == http.MethodPost && r.URL.Path == "/agent/jobs":
			var got PostJobRequest; decodeBody(t, r, &got)
			if got.PosterWallet != "poster" || got.RewardRTC != 12.5 || got.Title != "Research" { t.Fatalf("bad post payload: %+v", got) }
			seen["post"] = true; w.Write([]byte(`{"job_id":"job_1","status":"open"}`))
		case r.Method == http.MethodPost && r.URL.Path == "/agent/jobs/job_1/claim":
			var got ClaimJobRequest; decodeBody(t, r, &got)
			if got.WorkerWallet != "worker" { t.Fatalf("bad claim payload: %+v", got) }
			seen["claim"] = true; w.Write([]byte(`{"ok":true}`))
		case r.Method == http.MethodPost && r.URL.Path == "/agent/jobs/job_1/deliver":
			var got DeliverJobRequest; decodeBody(t, r, &got)
			if got.WorkerWallet != "worker" || got.DeliverableURL != "https://example.test/result" || got.DeliverableHash != "sha256:abc" { t.Fatalf("bad deliver payload: %+v", got) }
			seen["deliver"] = true; w.Write([]byte(`{"ok":true}`))
		case r.Method == http.MethodPost && r.URL.Path == "/agent/jobs/job_1/accept":
			var got AcceptJobRequest; decodeBody(t, r, &got)
			if got.PosterWallet != "poster" || got.Rating == nil || *got.Rating != 5 { t.Fatalf("bad accept payload: %+v", got) }
			seen["accept"] = true; w.Write([]byte(`{"status":"completed"}`))
		case r.Method == http.MethodPost && r.URL.Path == "/agent/jobs/job_2/dispute":
			var got DisputeJobRequest; decodeBody(t, r, &got)
			if got.PosterWallet != "poster" || got.Reason != "incomplete" { t.Fatalf("bad dispute payload: %+v", got) }
			seen["dispute"] = true; w.Write([]byte(`{"status":"disputed"}`))
		case r.Method == http.MethodPost && r.URL.Path == "/agent/jobs/job_3/cancel":
			var got CancelJobRequest; decodeBody(t, r, &got)
			if got.PosterWallet != "poster" { t.Fatalf("bad cancel payload: %+v", got) }
			seen["cancel"] = true; w.Write([]byte(`{"status":"cancelled"}`))
		default:
			http.Error(w, "unexpected", 500)
		}
	})
	defer ts.Close()
	ctx := context.Background()

	posted, err := c.PostJob(ctx, PostJobRequest{PosterWallet:"poster", Title:"Research", Description:"Do work", RewardRTC:12.5, Category:"research", TTLSeconds:3600})
	if err != nil || posted.JobID != "job_1" { t.Fatalf("PostJob: %+v %v", posted, err) }
	if _, err = c.ClaimJob(ctx, "job_1", "worker"); err != nil { t.Fatal(err) }
	if _, err = c.DeliverJob(ctx, "job_1", DeliverJobRequest{WorkerWallet:"worker", DeliverableURL:"https://example.test/result", ResultSummary:"done", DeliverableHash:"sha256:abc"}); err != nil { t.Fatal(err) }
	rating := 5
	if _, err = c.AcceptJob(ctx, "job_1", AcceptJobRequest{PosterWallet:"poster", Rating:&rating}); err != nil { t.Fatal(err) }
	if _, err = c.DisputeJob(ctx, "job_2", DisputeJobRequest{PosterWallet:"poster", Reason:"incomplete"}); err != nil { t.Fatal(err) }
	if _, err = c.CancelJob(ctx, "job_3", "poster"); err != nil { t.Fatal(err) }

	for _, key := range []string{"post","claim","deliver","accept","dispute","cancel"} { if !seen[key] { t.Errorf("missing request %s", key) } }
}

func TestReadEndpointsAndFilters(t *testing.T) {
	c, ts := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		switch r.URL.Path {
		case "/agent/jobs":
			q := r.URL.Query()
			if q.Get("status") != "open" || q.Get("category") != "code" || q.Get("limit") != "20" || q.Get("offset") != "3" || q.Get("min_reward") != "4.5" { t.Fatalf("bad query: %s", r.URL.RawQuery) }
			w.Write([]byte(`{"jobs":[{"job_id":"job_a","reward_rtc":9,"status":"open"}],"total":1}`))
		case "/agent/jobs/job_a":
			w.Write([]byte(`{"job_id":"job_a","title":"A","status":"open"}`))
		case "/agent/reputation/RTCabc":
			w.Write([]byte(`{"wallet":"RTCabc","trust_score":98,"trust_level":"legendary","total_rtc_earned":55}`))
		case "/agent/stats":
			w.Write([]byte(`{"stats":{"completed_jobs":4,"total_rtc_volume":123.5}}`))
		default: http.NotFound(w,r)
		}
	})
	defer ts.Close()
	ctx := context.Background()
	jobs, err := c.ListJobs(ctx, ListJobsOptions{Status:"open", Category:"code", Limit:20, Offset:3, MinReward:4.5})
	if err != nil || len(jobs.Jobs)!=1 || jobs.Jobs[0].JobID!="job_a" { t.Fatalf("jobs: %+v %v", jobs, err) }
	job, err := c.GetJob(ctx,"job_a"); if err!=nil || job.Title!="A" { t.Fatalf("job: %+v %v", job,err) }
	rep, err := c.GetReputation(ctx,"RTCabc"); if err!=nil || rep.TrustScore!=98 { t.Fatalf("rep: %+v %v",rep,err) }
	stats, err := c.GetStats(ctx); if err!=nil || stats.Stats["completed_jobs"].(float64)!=4 { t.Fatalf("stats: %+v %v",stats,err) }
}

func TestAPIErrorPreservesResponse(t *testing.T) {
	c, ts := testClient(t, func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusConflict); w.Write([]byte(`{"error":"job already claimed"}`)) })
	defer ts.Close()
	_, err := c.ClaimJob(context.Background(), "job_1", "worker")
	var apiErr *APIError
	if !errors.As(err, &apiErr) { t.Fatalf("expected APIError, got %T: %v", err, err) }
	if apiErr.StatusCode != http.StatusConflict || !strings.Contains(apiErr.Body,"already claimed") { t.Fatalf("bad APIError: %+v",apiErr) }
}

func TestValidationAndBaseURL(t *testing.T) {
	if _, err := NewClient("ftp://example.com", nil); err == nil { t.Fatal("expected scheme error") }
	c, err := NewClient("", &http.Client{})
	if err != nil { t.Fatal(err) }
	u, _ := url.Parse(DefaultBaseURL)
	if c.baseURL.Host != u.Host { t.Fatalf("default host = %q", c.baseURL.Host) }
	if _, err := c.GetJob(context.Background(), " "); err == nil { t.Fatal("expected empty job ID error") }
	if _, err := c.GetStats(nil); err == nil { t.Fatal("expected nil context error") }
}
