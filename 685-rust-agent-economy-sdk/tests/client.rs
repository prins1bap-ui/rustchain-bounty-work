use httpmock::prelude::*;
use rustchain_agent_economy::{
    AcceptJobRequest, AgentEconomyClient, BrowseJobsQuery, CancelJobRequest, ClaimJobRequest,
    DeliverJobRequest, DisputeJobRequest, PostJobRequest,
};
use serde_json::json;

#[tokio::test]
async fn browse_jobs_and_typed_filters_are_forwarded() {
    let plain_server = MockServer::start();
    let plain = plain_server.mock(|when, then| {
        when.method(GET).path("/agent/jobs");
        then.status(200).json_body(json!({"jobs": []}));
    });
    let plain_client = AgentEconomyClient::new(plain_server.base_url()).unwrap();
    assert_eq!(plain_client.browse_jobs().await.unwrap()["jobs"], json!([]));
    plain.assert();

    let filtered_server = MockServer::start();
    let filtered = filtered_server.mock(|when, then| {
        when.method(GET)
            .path("/agent/jobs")
            .query_param("category", "code")
            .query_param("status", "open")
            .query_param("limit", "25")
            .query_param("offset", "5")
            .query_param("min_reward", "10");
        then.status(200)
            .json_body(json!({"jobs": [{"job_id": "job_1"}]}));
    });
    let filtered_client = AgentEconomyClient::new(filtered_server.base_url()).unwrap();
    let query = BrowseJobsQuery {
        category: Some("code".into()),
        status: Some("open".into()),
        limit: Some(25),
        offset: Some(5),
        min_reward: Some(10.0),
    };
    assert_eq!(
        filtered_client
            .browse_jobs_filtered(&query)
            .await
            .unwrap()["jobs"][0]["job_id"],
        "job_1"
    );
    filtered.assert();
}

#[tokio::test]
async fn raw_query_escape_hatch_remains_available() {
    let server = MockServer::start();
    let mock = server.mock(|when, then| {
        when.method(GET)
            .path("/agent/jobs")
            .query_param("future_filter", "value");
        then.status(200).json_body(json!({"jobs": []}));
    });
    let client = AgentEconomyClient::new(server.base_url()).unwrap();
    let query = vec![("future_filter".to_string(), "value".to_string())];
    client.browse_jobs_with_query(&query).await.unwrap();
    mock.assert();
}

#[tokio::test]
async fn reads_job_reputation_and_stats() {
    let server = MockServer::start();
    let job = server.mock(|when, then| {
        when.method(GET).path("/agent/jobs/job_abc");
        then.status(200).json_body(json!({"job_id": "job_abc"}));
    });
    let reputation = server.mock(|when, then| {
        when.method(GET).path("/agent/reputation/RTCabc");
        then.status(200).json_body(json!({"trust_score": 100}));
    });
    let stats = server.mock(|when, then| {
        when.method(GET).path("/agent/stats");
        then.status(200).json_body(json!({"total_jobs": 2}));
    });
    let client = AgentEconomyClient::new(server.base_url()).unwrap();
    assert_eq!(client.job("job_abc").await.unwrap()["job_id"], "job_abc");
    assert_eq!(
        client.reputation("RTCabc").await.unwrap()["trust_score"],
        100
    );
    assert_eq!(client.stats().await.unwrap()["total_jobs"], 2);
    job.assert();
    reputation.assert();
    stats.assert();
}

#[tokio::test]
async fn current_post_claim_and_deliver_contracts_match_mock_payloads() {
    let server = MockServer::start();
    let post = server.mock(|when, then| {
        when.method(POST).path("/agent/jobs").json_body(json!({
            "poster_wallet": "RTCposter",
            "title": "Write docs",
            "description": "Write a complete SDK usage guide.",
            "category": "writing",
            "reward_rtc": 5.0,
            "ttl_seconds": 7200,
            "tags": ["docs", "sdk"]
        }));
        then.status(201).json_body(json!({"job_id": "job_new"}));
    });
    let claim = server.mock(|when, then| {
        when.method(POST)
            .path("/agent/jobs/job_1/claim")
            .json_body(json!({"worker_wallet": "RTCworker"}));
        then.status(200).json_body(json!({"status": "claimed"}));
    });
    let deliver = server.mock(|when, then| {
        when.method(POST)
            .path("/agent/jobs/job_1/deliver")
            .json_body(json!({
                "worker_wallet": "RTCworker",
                "deliverable_url": "https://example.com/work",
                "deliverable_hash": "sha256:abc"
            }));
        then.status(200).json_body(json!({"status": "delivered"}));
    });
    let client = AgentEconomyClient::new(server.base_url()).unwrap();
    assert_eq!(
        client
            .post_job(&PostJobRequest {
                poster_wallet: "RTCposter".into(),
                title: "Write docs".into(),
                description: "Write a complete SDK usage guide.".into(),
                category: "writing".into(),
                reward_rtc: 5.0,
                ttl_seconds: Some(7200),
                tags: Some(vec!["docs".into(), "sdk".into()]),
            })
            .await
            .unwrap()["job_id"],
        "job_new"
    );
    assert_eq!(
        client
            .claim_job(
                "job_1",
                &ClaimJobRequest {
                    worker_wallet: "RTCworker".into(),
                },
            )
            .await
            .unwrap()["status"],
        "claimed"
    );
    assert_eq!(
        client
            .deliver_job(
                "job_1",
                &DeliverJobRequest {
                    worker_wallet: "RTCworker".into(),
                    deliverable_url: Some("https://example.com/work".into()),
                    deliverable_hash: Some("sha256:abc".into()),
                    result_summary: None,
                },
            )
            .await
            .unwrap()["status"],
        "delivered"
    );
    post.assert();
    claim.assert();
    deliver.assert();
}

#[tokio::test]
async fn typed_accept_dispute_and_cancel_contracts_match_current_main() {
    let server = MockServer::start();
    let accept = server.mock(|when, then| {
        when.method(POST)
            .path("/agent/jobs/job_1/accept")
            .json_body(json!({"poster_wallet": "RTCposter", "rating": 5}));
        then.status(200).json_body(json!({"status": "completed"}));
    });
    let dispute = server.mock(|when, then| {
        when.method(POST)
            .path("/agent/jobs/job_2/dispute")
            .json_body(json!({"poster_wallet": "RTCposter", "reason": "incomplete"}));
        then.status(200).json_body(json!({"status": "disputed"}));
    });
    let cancel = server.mock(|when, then| {
        when.method(POST)
            .path("/agent/jobs/job_3/cancel")
            .json_body(json!({"poster_wallet": "RTCposter"}));
        then.status(200).json_body(json!({"status": "cancelled"}));
    });
    let client = AgentEconomyClient::new(server.base_url()).unwrap();
    assert_eq!(
        client
            .accept_job(
                "job_1",
                &AcceptJobRequest {
                    poster_wallet: "RTCposter".into(),
                    rating: Some(5),
                },
            )
            .await
            .unwrap()["status"],
        "completed"
    );
    assert_eq!(
        client
            .dispute_job(
                "job_2",
                &DisputeJobRequest {
                    poster_wallet: "RTCposter".into(),
                    reason: "incomplete".into(),
                },
            )
            .await
            .unwrap()["status"],
        "disputed"
    );
    assert_eq!(
        client
            .cancel_job(
                "job_3",
                &CancelJobRequest {
                    poster_wallet: "RTCposter".into(),
                },
            )
            .await
            .unwrap()["status"],
        "cancelled"
    );
    accept.assert();
    dispute.assert();
    cancel.assert();
}

#[tokio::test]
async fn current_contract_validation_fails_before_network() {
    let client = AgentEconomyClient::new("https://example.invalid").unwrap();
    assert!(client.job("../bad").await.is_err());
    assert!(client.reputation("wallet/bad").await.is_err());

    let base = PostJobRequest {
        poster_wallet: "RTCposter".into(),
        title: "Valid title".into(),
        description: "This description is long enough.".into(),
        category: "code".into(),
        reward_rtc: 1.0,
        ttl_seconds: None,
        tags: None,
    };

    let mut bad_title = base.clone();
    bad_title.title = "x".into();
    assert!(client.post_job(&bad_title).await.is_err());

    let mut bad_description = base.clone();
    bad_description.description = "short".into();
    assert!(client.post_job(&bad_description).await.is_err());

    let mut bad_category = base.clone();
    bad_category.category = "made-up".into();
    assert!(client.post_job(&bad_category).await.is_err());

    let mut bad_reward = base.clone();
    bad_reward.reward_rtc = 0.001;
    assert!(client.post_job(&bad_reward).await.is_err());

    assert!(client
        .deliver_job(
            "job_1",
            &DeliverJobRequest {
                worker_wallet: "RTCworker".into(),
                deliverable_url: None,
                deliverable_hash: Some("hash-only-is-not-enough".into()),
                result_summary: None,
            },
        )
        .await
        .is_err());

    assert!(client
        .accept_job(
            "job_1",
            &AcceptJobRequest {
                poster_wallet: "RTCposter".into(),
                rating: Some(9),
            },
        )
        .await
        .is_err());

    assert!(client
        .browse_jobs_filtered(&BrowseJobsQuery {
            category: Some("invalid".into()),
            ..BrowseJobsQuery::default()
        })
        .await
        .is_err());
}

#[tokio::test]
async fn non_success_body_is_preserved_for_diagnostics() {
    let server = MockServer::start();
    let mock = server.mock(|when, then| {
        when.method(GET).path("/agent/stats");
        then.status(503).body("node restarting");
    });
    let client = AgentEconomyClient::new(server.base_url()).unwrap();
    let error = client.stats().await.unwrap_err().to_string();
    assert!(error.contains("503"));
    assert!(error.contains("node restarting"));
    mock.assert();
}
