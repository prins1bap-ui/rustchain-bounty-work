package agenteconomy

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"
)

const DefaultBaseURL = "https://rustchain.org"

// Client is a context-aware client for the RustChain RIP-302 Agent Economy API.
type Client struct {
	baseURL    *url.URL
	httpClient *http.Client
}

// APIError preserves the HTTP status and response body returned by the node.
type APIError struct {
	StatusCode int
	Status     string
	Body       string
}

func (e *APIError) Error() string {
	if e.Body == "" {
		return fmt.Sprintf("agent economy API: %s", e.Status)
	}
	return fmt.Sprintf("agent economy API: %s: %s", e.Status, e.Body)
}

// NewClient constructs a client. Empty baseURL uses https://rustchain.org.
func NewClient(baseURL string, httpClient *http.Client) (*Client, error) {
	if strings.TrimSpace(baseURL) == "" {
		baseURL = DefaultBaseURL
	}
	parsed, err := url.Parse(strings.TrimRight(baseURL, "/"))
	if err != nil {
		return nil, fmt.Errorf("parse base URL: %w", err)
	}
	if parsed.Scheme != "http" && parsed.Scheme != "https" {
		return nil, fmt.Errorf("base URL must use http or https")
	}
	if parsed.Host == "" {
		return nil, fmt.Errorf("base URL requires a host")
	}
	if httpClient == nil {
		httpClient = &http.Client{Timeout: 30 * time.Second}
	}
	return &Client{baseURL: parsed, httpClient: httpClient}, nil
}

type PostJobRequest struct {
	PosterWallet string   `json:"poster_wallet"`
	Title        string   `json:"title"`
	Description  string   `json:"description"`
	RewardRTC    float64  `json:"reward_rtc"`
	Category     string   `json:"category,omitempty"`
	TTLSeconds   int      `json:"ttl_seconds,omitempty"`
	Tags         []string `json:"tags,omitempty"`
}

type ClaimJobRequest struct {
	WorkerWallet string `json:"worker_wallet"`
}

type DeliverJobRequest struct {
	WorkerWallet   string `json:"worker_wallet"`
	DeliverableURL string `json:"deliverable_url,omitempty"`
	ResultSummary  string `json:"result_summary,omitempty"`
	DeliverableHash string `json:"deliverable_hash,omitempty"`
}

type AcceptJobRequest struct {
	PosterWallet string `json:"poster_wallet"`
	Rating       *int   `json:"rating,omitempty"`
}

type DisputeJobRequest struct {
	PosterWallet string `json:"poster_wallet"`
	Reason       string `json:"reason"`
}

type CancelJobRequest struct {
	PosterWallet string `json:"poster_wallet"`
}

type ListJobsOptions struct {
	Status    string
	Category  string
	Limit     int
	Offset    int
	MinReward float64
}

// Envelope is intentionally permissive because the live API has accumulated
// fields over time. Typed common fields are exposed while Raw retains the full response.
type Envelope struct {
	OK      bool              `json:"ok,omitempty"`
	JobID   string            `json:"job_id,omitempty"`
	Status  string            `json:"status,omitempty"`
	Message string            `json:"message,omitempty"`
	Error   string            `json:"error,omitempty"`
	Raw     map[string]any    `json:"-"`
}

type Job struct {
	JobID          string         `json:"job_id,omitempty"`
	PosterWallet   string         `json:"poster_wallet,omitempty"`
	WorkerWallet   string         `json:"worker_wallet,omitempty"`
	Title          string         `json:"title,omitempty"`
	Description    string         `json:"description,omitempty"`
	Category       string         `json:"category,omitempty"`
	RewardRTC      float64        `json:"reward_rtc,omitempty"`
	Status         string         `json:"status,omitempty"`
	Tags           []string       `json:"tags,omitempty"`
	DeliverableURL string         `json:"deliverable_url,omitempty"`
	ResultSummary  string         `json:"result_summary,omitempty"`
	CreatedAt      any            `json:"created_at,omitempty"`
	ExpiresAt      any            `json:"expires_at,omitempty"`
	Raw            map[string]any `json:"-"`
}

type JobsResponse struct {
	Jobs   []Job          `json:"jobs"`
	Count  int            `json:"count,omitempty"`
	Total  int            `json:"total,omitempty"`
	Raw    map[string]any `json:"-"`
}

type ReputationResponse struct {
	Wallet         string         `json:"wallet,omitempty"`
	TrustScore     float64        `json:"trust_score,omitempty"`
	TrustLevel     string         `json:"trust_level,omitempty"`
	AvgRating      float64        `json:"avg_rating,omitempty"`
	TotalRTCEarned float64        `json:"total_rtc_earned,omitempty"`
	CompletedJobs  int            `json:"completed_jobs,omitempty"`
	Raw            map[string]any `json:"-"`
}

type StatsResponse struct {
	Stats map[string]any `json:"stats,omitempty"`
	Raw   map[string]any `json:"-"`
}

func (c *Client) PostJob(ctx context.Context, req PostJobRequest) (*Envelope, error) {
	return c.action(ctx, http.MethodPost, "/agent/jobs", req)
}

func (c *Client) ListJobs(ctx context.Context, opts ListJobsOptions) (*JobsResponse, error) {
	q := url.Values{}
	if opts.Status != "" { q.Set("status", opts.Status) }
	if opts.Category != "" { q.Set("category", opts.Category) }
	if opts.Limit > 0 { q.Set("limit", strconv.Itoa(opts.Limit)) }
	if opts.Offset > 0 { q.Set("offset", strconv.Itoa(opts.Offset)) }
	if opts.MinReward > 0 { q.Set("min_reward", strconv.FormatFloat(opts.MinReward, 'f', -1, 64)) }
	path := "/agent/jobs"
	if encoded := q.Encode(); encoded != "" { path += "?" + encoded }
	var out JobsResponse
	raw, err := c.doJSON(ctx, http.MethodGet, path, nil, &out)
	if err != nil { return nil, err }
	out.Raw = raw
	return &out, nil
}

func (c *Client) GetJob(ctx context.Context, jobID string) (*Job, error) {
	if err := validateID("job ID", jobID); err != nil { return nil, err }
	var out Job
	raw, err := c.doJSON(ctx, http.MethodGet, "/agent/jobs/"+url.PathEscape(jobID), nil, &out)
	if err != nil { return nil, err }
	out.Raw = raw
	return &out, nil
}

func (c *Client) ClaimJob(ctx context.Context, jobID, workerWallet string) (*Envelope, error) {
	if err := validateID("job ID", jobID); err != nil { return nil, err }
	return c.action(ctx, http.MethodPost, "/agent/jobs/"+url.PathEscape(jobID)+"/claim", ClaimJobRequest{WorkerWallet: workerWallet})
}

func (c *Client) DeliverJob(ctx context.Context, jobID string, req DeliverJobRequest) (*Envelope, error) {
	if err := validateID("job ID", jobID); err != nil { return nil, err }
	return c.action(ctx, http.MethodPost, "/agent/jobs/"+url.PathEscape(jobID)+"/deliver", req)
}

func (c *Client) AcceptJob(ctx context.Context, jobID string, req AcceptJobRequest) (*Envelope, error) {
	if err := validateID("job ID", jobID); err != nil { return nil, err }
	return c.action(ctx, http.MethodPost, "/agent/jobs/"+url.PathEscape(jobID)+"/accept", req)
}

func (c *Client) DisputeJob(ctx context.Context, jobID string, req DisputeJobRequest) (*Envelope, error) {
	if err := validateID("job ID", jobID); err != nil { return nil, err }
	return c.action(ctx, http.MethodPost, "/agent/jobs/"+url.PathEscape(jobID)+"/dispute", req)
}

func (c *Client) CancelJob(ctx context.Context, jobID, posterWallet string) (*Envelope, error) {
	if err := validateID("job ID", jobID); err != nil { return nil, err }
	return c.action(ctx, http.MethodPost, "/agent/jobs/"+url.PathEscape(jobID)+"/cancel", CancelJobRequest{PosterWallet: posterWallet})
}

func (c *Client) GetReputation(ctx context.Context, wallet string) (*ReputationResponse, error) {
	if err := validateID("wallet", wallet); err != nil { return nil, err }
	var out ReputationResponse
	raw, err := c.doJSON(ctx, http.MethodGet, "/agent/reputation/"+url.PathEscape(wallet), nil, &out)
	if err != nil { return nil, err }
	out.Raw = raw
	return &out, nil
}

func (c *Client) GetStats(ctx context.Context) (*StatsResponse, error) {
	var out StatsResponse
	raw, err := c.doJSON(ctx, http.MethodGet, "/agent/stats", nil, &out)
	if err != nil { return nil, err }
	out.Raw = raw
	return &out, nil
}

func (c *Client) action(ctx context.Context, method, path string, body any) (*Envelope, error) {
	var out Envelope
	raw, err := c.doJSON(ctx, method, path, body, &out)
	if err != nil { return nil, err }
	out.Raw = raw
	return &out, nil
}

func (c *Client) doJSON(ctx context.Context, method, path string, body any, out any) (map[string]any, error) {
	if ctx == nil { return nil, errors.New("context is required") }
	u := *c.baseURL
	u.Path = strings.TrimRight(c.baseURL.Path, "/") + strings.SplitN(path, "?", 2)[0]
	if parts := strings.SplitN(path, "?", 2); len(parts) == 2 { u.RawQuery = parts[1] }

	var reader io.Reader
	if body != nil {
		payload, err := json.Marshal(body)
		if err != nil { return nil, fmt.Errorf("encode request: %w", err) }
		reader = bytes.NewReader(payload)
	}
	req, err := http.NewRequestWithContext(ctx, method, u.String(), reader)
	if err != nil { return nil, fmt.Errorf("create request: %w", err) }
	req.Header.Set("Accept", "application/json")
	if body != nil { req.Header.Set("Content-Type", "application/json") }

	resp, err := c.httpClient.Do(req)
	if err != nil { return nil, fmt.Errorf("agent economy request: %w", err) }
	defer resp.Body.Close()
	data, err := io.ReadAll(io.LimitReader(resp.Body, 4<<20))
	if err != nil { return nil, fmt.Errorf("read response: %w", err) }
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, &APIError{StatusCode: resp.StatusCode, Status: resp.Status, Body: strings.TrimSpace(string(data))}
	}
	if len(bytes.TrimSpace(data)) == 0 { return map[string]any{}, nil }
	var raw map[string]any
	if err := json.Unmarshal(data, &raw); err != nil { return nil, fmt.Errorf("decode response: %w", err) }
	if out != nil {
		if err := json.Unmarshal(data, out); err != nil { return nil, fmt.Errorf("decode typed response: %w", err) }
	}
	return raw, nil
}

func validateID(name, value string) error {
	if strings.TrimSpace(value) == "" { return fmt.Errorf("%s is required", name) }
	return nil
}
