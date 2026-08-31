use httpmock::prelude::*;
use rustchain_agent_economy::{
    AgentEconomyClient, ClaimJobRequest, DeliverJobRequest, PostJobRequest,
};
use serde_json::json;

#[tokio::test]
async fn browse_jobs_and_explicit_query_are_forwarded() {
    let server = MockServer::start();
    let plain = server.mock(|when, then| {
        when.method(GET).path("/agent/jobs");
        then.status(200).json_body(json!({"jobs": []}));
    });
    let filtered = server.mock(|when, then| {
        when.method(GET)
            .path("/agent/jobs")
            .query_param("status", "open")
            .query_param("limit", "25");
        then.status(200)
            .json_body(json!({"jobs": [{"job_id": "job_1"}]}));
    });
    let client = AgentEconomyClient::new(server.base_url()).unwrap();
    assert_eq!(client.browse_jobs().await.unwrap()["jobs"], json!([]));
    let query = vec![
        ("status".to_string(), "open".to_string()),
        ("limit".to_string(), "25".to_string()),
    ];
    assert_eq!(
        client.browse_jobs_with_query(&query).await.unwrap()["jobs"][0]["job_id"],
        "job_1"
    );
    plain.assert();
    filtered.assert();
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
async fn documented_mutating_examples_match_exact_routes_and_payloads_on_mock_only() {
    let server = MockServer::start();
    let post = server.mock(|when, then| {
        when.method(POST).path("/agent/jobs").json_body(json!({
            "poster_wallet": "RTCposter",
            "title": "Write docs",
            "category": "writing",
            "reward_rtc": 5.0
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
                "result_summary": "Done"
            }));
        then.status(200).json_body(json!({"status": "delivered"}));
    });
    let client = AgentEconomyClient::new(server.base_url()).unwrap();
    assert_eq!(
        client
            .post_job(&PostJobRequest {
                poster_wallet: "RTCposter".into(),
                title: "Write docs".into(),
                category: "writing".into(),
                reward_rtc: 5.0,
                description: None,
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
                    deliverable_url: "https://example.com/work".into(),
                    result_summary: "Done".into(),
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
async fn undocumented_action_bodies_are_caller_controlled_and_mocked_only() {
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
            .accept_job("job_1", &json!({"poster_wallet": "RTCposter", "rating": 5}))
            .await
            .unwrap()["status"],
        "completed"
    );
    assert_eq!(
        client
            .dispute_job(
                "job_2",
                &json!({"poster_wallet": "RTCposter", "reason": "incomplete"}),
            )
            .await
            .unwrap()["status"],
        "disputed"
    );
    assert_eq!(
        client
            .cancel_job("job_3", &json!({"poster_wallet": "RTCposter"}))
            .await
            .unwrap()["status"],
        "cancelled"
    );
    accept.assert();
    dispute.assert();
    cancel.assert();
}

#[tokio::test]
async fn invalid_inputs_fail_before_network() {
    let client = AgentEconomyClient::new("https://example.invalid").unwrap();
    assert!(client.job("../bad").await.is_err());
    assert!(client.reputation("wallet/bad").await.is_err());
    assert!(client
        .post_job(&PostJobRequest {
            poster_wallet: "RTCposter".into(),
            title: "x".into(),
            category: "code".into(),
            reward_rtc: 0.0,
            description: None,
        })
        .await
        .is_err());
    assert!(client.accept_job("job_1", &json!(["not", "an", "object"])).await.is_err());
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
