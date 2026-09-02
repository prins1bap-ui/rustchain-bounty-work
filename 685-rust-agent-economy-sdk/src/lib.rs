use reqwest::{Client, StatusCode};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::time::Duration;
use thiserror::Error;

pub const DEFAULT_BASE_URL: &str = "https://50.28.86.131";
pub const VALID_CATEGORIES: &[&str] = &[
    "research",
    "code",
    "video",
    "audio",
    "writing",
    "translation",
    "data",
    "design",
    "testing",
    "other",
];

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
    pub description: String,
    pub category: String,
    pub reward_rtc: f64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ttl_seconds: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tags: Option<Vec<String>>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct ClaimJobRequest {
    pub worker_wallet: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct DeliverJobRequest {
    pub worker_wallet: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub deliverable_url: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub deliverable_hash: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub result_summary: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct AcceptJobRequest {
    pub poster_wallet: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub rating: Option<u8>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct DisputeJobRequest {
    pub poster_wallet: String,
    pub reason: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct CancelJobRequest {
    pub poster_wallet: String,
}

#[derive(Clone, Debug, Default, Serialize, Deserialize, PartialEq)]
pub struct BrowseJobsQuery {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub category: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub status: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub limit: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub offset: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub min_reward: Option<f64>,
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

    /// Typed query support for the current `GET /agent/jobs` contract.
    pub async fn browse_jobs_filtered(&self, query: &BrowseJobsQuery) -> Result<Value> {
        validate_browse_query(query)?;
        let response = self
            .http
            .get(self.endpoint("/agent/jobs"))
            .query(query)
            .send()
            .await?;
        parse_json(response).await
    }

    /// Escape hatch for forward-compatible query parameters not yet modeled by this crate.
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
        if request.title.trim().chars().count() < 5 {
            return Err(AgentEconomyError::InvalidArgument(
                "title must be at least 5 characters".into(),
            ));
        }
        if request.description.trim().chars().count() < 20 {
            return Err(AgentEconomyError::InvalidArgument(
                "description must be at least 20 characters".into(),
            ));
        }
        let category = request.category.trim().to_ascii_lowercase();
        if !VALID_CATEGORIES.contains(&category.as_str()) {
            return Err(AgentEconomyError::InvalidArgument(format!(
                "category must be one of: {}",
                VALID_CATEGORIES.join(", ")
            )));
        }
        if !request.reward_rtc.is_finite() || !(0.01..=10000.0).contains(&request.reward_rtc) {
            return Err(AgentEconomyError::InvalidArgument(
                "reward_rtc must be finite and between 0.01 and 10000".into(),
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
        let has_url = has_text(request.deliverable_url.as_deref());
        let has_summary = has_text(request.result_summary.as_deref());
        if !has_url && !has_summary {
            return Err(AgentEconomyError::InvalidArgument(
                "deliverable_url or result_summary required".into(),
            ));
        }
        let job_id = validate_path_component("job_id", job_id)?;
        self.post_json(&format!("/agent/jobs/{job_id}/deliver"), request)
            .await
    }

    /// Mutating endpoint: accepting a delivery releases escrow on a live node.
    pub async fn accept_job(&self, job_id: &str, request: &AcceptJobRequest) -> Result<Value> {
        validate_nonempty("poster_wallet", &request.poster_wallet)?;
        if let Some(rating) = request.rating {
            if !(1..=5).contains(&rating) {
                return Err(AgentEconomyError::InvalidArgument(
                    "rating must be between 1 and 5".into(),
                ));
            }
        }
        let job_id = validate_path_component("job_id", job_id)?;
        self.post_json(&format!("/agent/jobs/{job_id}/accept"), request)
            .await
    }

    /// Mutating endpoint: disputing a delivered job holds escrow pending resolution.
    pub async fn dispute_job(&self, job_id: &str, request: &DisputeJobRequest) -> Result<Value> {
        validate_nonempty("poster_wallet", &request.poster_wallet)?;
        validate_nonempty("reason", &request.reason)?;
        let job_id = validate_path_component("job_id", job_id)?;
        self.post_json(&format!("/agent/jobs/{job_id}/dispute"), request)
            .await
    }

    /// Mutating endpoint: cancellation may refund escrow on a live node.
    pub async fn cancel_job(&self, job_id: &str, request: &CancelJobRequest) -> Result<Value> {
        validate_nonempty("poster_wallet", &request.poster_wallet)?;
        let job_id = validate_path_component("job_id", job_id)?;
        self.post_json(&format!("/agent/jobs/{job_id}/cancel"), request)
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

fn validate_browse_query(query: &BrowseJobsQuery) -> Result<()> {
    if let Some(category) = &query.category {
        let category = category.trim().to_ascii_lowercase();
        if !VALID_CATEGORIES.contains(&category.as_str()) {
            return Err(AgentEconomyError::InvalidArgument(format!(
                "category must be one of: {}",
                VALID_CATEGORIES.join(", ")
            )));
        }
    }
    if let Some(min_reward) = query.min_reward {
        if !min_reward.is_finite() || min_reward < 0.0 {
            return Err(AgentEconomyError::InvalidArgument(
                "min_reward must be a non-negative finite number".into(),
            ));
        }
    }
    Ok(())
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

fn has_text(value: Option<&str>) -> bool {
    value.is_some_and(|value| !value.trim().is_empty())
}
