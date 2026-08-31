use reqwest::{Client, StatusCode};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::time::Duration;
use thiserror::Error;

pub const DEFAULT_BASE_URL: &str = "https://50.28.86.131";

#[derive(Debug, Error)]
pub enum AgentEconomyError {
    #[error("HTTP request failed: {0}")]
    Http(#[from] reqwest::Error),
    #[error("Agent Economy API returned HTTP {status}: {body}")]
    Api { status: StatusCode, body: String },
    #[error("invalid argument: {0}")]
    InvalidArgument(String),
    #[error("Agent Economy API returned a non-JSON success body: {0}")]
    InvalidJson(#[from] serde_json::Error),
}

pub type Result<T> = std::result::Result<T, AgentEconomyError>;

#[derive(Clone, Debug)]
pub struct AgentEconomyClient {
    base_url: String,
    http: Client,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct PostJobRequest {
    pub poster_wallet: String,
    pub title: String,
    pub category: String,
    pub reward_rtc: f64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct ClaimJobRequest {
    pub worker_wallet: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct DeliverJobRequest {
    pub worker_wallet: String,
    pub deliverable_url: String,
    pub result_summary: String,
}

impl AgentEconomyClient {
    pub fn new(base_url: impl Into<String>) -> Result<Self> {
        let base_url = normalize_base_url(base_url.into())?;
        let http = Client::builder().timeout(Duration::from_secs(20)).build()?;
        Ok(Self { base_url, http })
    }

    pub fn with_client(base_url: impl Into<String>, http: Client) -> Result<Self> {
        Ok(Self {
            base_url: normalize_base_url(base_url.into())?,
            http,
        })
    }

    pub fn default_node() -> Result<Self> {
        Self::new(DEFAULT_BASE_URL)
    }

    pub async fn browse_jobs(&self) -> Result<Value> {
        let response = self.http.get(self.endpoint("/agent/jobs")).send().await?;
        parse_json(response).await
    }

    /// Sends caller-supplied query parameters without inventing undocumented semantics.
    pub async fn browse_jobs_with_query(&self, query: &[(String, String)]) -> Result<Value> {
        let response = self
            .http
            .get(self.endpoint("/agent/jobs"))
            .query(query)
            .send()
            .await?;
        parse_json(response).await
    }

    pub async fn job(&self, job_id: &str) -> Result<Value> {
        let job_id = validate_path_component("job_id", job_id)?;
        let response = self
            .http
            .get(self.endpoint(&format!("/agent/jobs/{job_id}")))
            .send()
            .await?;
        parse_json(response).await
    }

    pub async fn reputation(&self, wallet: &str) -> Result<Value> {
        let wallet = validate_path_component("wallet", wallet)?;
        let response = self
            .http
            .get(self.endpoint(&format!("/agent/reputation/{wallet}")))
            .send()
            .await?;
        parse_json(response).await
    }

    pub async fn stats(&self) -> Result<Value> {
        let response = self.http.get(self.endpoint("/agent/stats")).send().await?;
        parse_json(response).await
    }

    /// Mutating endpoint: posting a job can lock escrow on a live node.
    pub async fn post_job(&self, request: &PostJobRequest) -> Result<Value> {
        validate_nonempty("poster_wallet", &request.poster_wallet)?;
        validate_nonempty("title", &request.title)?;
        validate_nonempty("category", &request.category)?;
        if !request.reward_rtc.is_finite() || request.reward_rtc <= 0.0 {
            return Err(AgentEconomyError::InvalidArgument(
                "reward_rtc must be finite and > 0".into(),
            ));
        }
        self.post_json("/agent/jobs", request).await
    }

    /// Mutating endpoint: claiming changes live marketplace state.
    pub async fn claim_job(&self, job_id: &str, request: &ClaimJobRequest) -> Result<Value> {
        validate_nonempty("worker_wallet", &request.worker_wallet)?;
        let job_id = validate_path_component("job_id", job_id)?;
        self.post_json(&format!("/agent/jobs/{job_id}/claim"), request)
            .await
    }

    /// Mutating endpoint: delivering changes live marketplace state.
    pub async fn deliver_job(&self, job_id: &str, request: &DeliverJobRequest) -> Result<Value> {
        validate_nonempty("worker_wallet", &request.worker_wallet)?;
        validate_nonempty("deliverable_url", &request.deliverable_url)?;
        validate_nonempty("result_summary", &request.result_summary)?;
        let job_id = validate_path_component("job_id", job_id)?;
        self.post_json(&format!("/agent/jobs/{job_id}/deliver"), request)
            .await
    }

    /// Mutating endpoint. The current bounty documents the route but not its JSON schema,
    /// so the SDK deliberately accepts an explicit caller-provided JSON object rather than
    /// hallucinating request fields.
    pub async fn accept_job(&self, job_id: &str, body: &Value) -> Result<Value> {
        self.post_action(job_id, "accept", body).await
    }

    /// Mutating endpoint with caller-provided JSON because #685 does not document the body.
    pub async fn dispute_job(&self, job_id: &str, body: &Value) -> Result<Value> {
        self.post_action(job_id, "dispute", body).await
    }

    /// Mutating endpoint with caller-provided JSON because #685 does not document the body.
    pub async fn cancel_job(&self, job_id: &str, body: &Value) -> Result<Value> {
        self.post_action(job_id, "cancel", body).await
    }

    async fn post_action(&self, job_id: &str, action: &str, body: &Value) -> Result<Value> {
        let job_id = validate_path_component("job_id", job_id)?;
        if !body.is_object() {
            return Err(AgentEconomyError::InvalidArgument(
                "action body must be a JSON object".into(),
            ));
        }
        self.post_json(&format!("/agent/jobs/{job_id}/{action}"), body)
            .await
    }

    async fn post_json<T: Serialize + ?Sized>(&self, path: &str, body: &T) -> Result<Value> {
        let response = self
            .http
            .post(self.endpoint(path))
            .json(body)
            .send()
            .await?;
        parse_json(response).await
    }

    fn endpoint(&self, path: &str) -> String {
        format!("{}{}", self.base_url, path)
    }
}

async fn parse_json(response: reqwest::Response) -> Result<Value> {
    let status = response.status();
    let body = response.text().await?;
    if !status.is_success() {
        return Err(AgentEconomyError::Api { status, body });
    }
    Ok(serde_json::from_str(&body)?)
}

fn normalize_base_url(value: String) -> Result<String> {
    let value = value.trim().trim_end_matches('/').to_string();
    if value.is_empty() {
        return Err(AgentEconomyError::InvalidArgument(
            "base_url must not be empty".into(),
        ));
    }
    if !(value.starts_with("https://") || value.starts_with("http://")) {
        return Err(AgentEconomyError::InvalidArgument(
            "base_url must start with http:// or https://".into(),
        ));
    }
    Ok(value)
}

fn validate_nonempty(name: &str, value: &str) -> Result<()> {
    if value.trim().is_empty() {
        return Err(AgentEconomyError::InvalidArgument(format!(
            "{name} must not be empty"
        )));
    }
    Ok(())
}

fn validate_path_component<'a>(name: &str, value: &'a str) -> Result<&'a str> {
    validate_nonempty(name, value)?;
    if value.contains('/') || value.contains('?') || value.contains('#') {
        return Err(AgentEconomyError::InvalidArgument(format!(
            "{name} contains path/query delimiters"
        )));
    }
    Ok(value)
}
