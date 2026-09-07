from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone

BASE = "https://api.apify.com"
RESULT_PATH = "apify_cloud_qa_result.json"
ACTOR_NAME = "website-tech-contact-snapshot"
EXPECTED_EVENT = "website-audit"
EXPECTED_EVENT_PRICE = Decimal("0.001")
TERMINAL_RUN_STATUSES = {"SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"}


def emit(payload: dict, code: int = 0) -> int:
    payload.setdefault("actor_name", ACTOR_NAME)
    payload.setdefault("unauthorized_spend_usd", 0)
    with open(RESULT_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
    print(json.dumps(payload, sort_keys=True))
    return code


def request_json(method: str, path: str, token: str, body=None):
    data = None
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "apify-cloud-qa/0.1",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=70) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": {"type": "http_error", "status": exc.code}}
    except Exception as exc:  # pragma: no cover
        return 0, {"error": {"type": exc.__class__.__name__}}


def dec(value):
    try:
        return Decimal(str(value)) if value is not None else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def effective_pricing_info(actor: dict):
    infos = actor.get("pricingInfos") or []
    now = datetime.now(timezone.utc)
    eligible = []
    for info in infos:
        started = parse_time(info.get("startedAt"))
        if started is None or started <= now:
            eligible.append((started or datetime.min.replace(tzinfo=timezone.utc), info))
    if not eligible:
        return None
    eligible.sort(key=lambda pair: pair[0])
    return eligible[-1][1]


def pricing_gate(actor: dict):
    info = effective_pricing_info(actor)
    if not info:
        return False, {"reason": "No effective pricingInfo is exposed by the Actor API."}
    model = info.get("pricingModel")
    evidence = {"pricing_model": model}
    if model != "PAY_PER_EVENT":
        evidence["reason"] = "Cloud QA blocked because effective pricing is not PAY_PER_EVENT."
        return False, evidence

    pricing = (info.get("pricingPerEvent") or {}).get("actorChargeEvents") or {}
    safe_events = {}
    for name, event in pricing.items():
        safe_events[name] = {
            "eventPriceUsd": event.get("eventPriceUsd"),
            "isPrimaryEvent": event.get("isPrimaryEvent"),
            "isOneTimeEvent": event.get("isOneTimeEvent"),
            "hasTieredPricing": bool(event.get("eventTieredPricingUsd")),
        }
    evidence["events"] = safe_events

    expected = pricing.get(EXPECTED_EVENT)
    if not expected:
        evidence["reason"] = "Required website-audit event is absent."
        return False, evidence
    if expected.get("eventTieredPricingUsd"):
        evidence["reason"] = "website-audit uses tiered pricing; exact $0.001 contract cannot be proven."
        return False, evidence
    if dec(expected.get("eventPriceUsd")) != EXPECTED_EVENT_PRICE:
        evidence["reason"] = "website-audit price is not exactly $0.001."
        return False, evidence

    for synthetic in ("apify-actor-start", "apify-default-dataset-item"):
        event = pricing.get(synthetic)
        if not event:
            continue
        if event.get("eventTieredPricingUsd"):
            evidence["reason"] = f"Synthetic event {synthetic} has tiered pricing and is not provably free."
            return False, evidence
        price = dec(event.get("eventPriceUsd"))
        if price is not None and price != 0:
            evidence["reason"] = f"Synthetic event {synthetic} is non-zero and would violate invalid/failed uncharged contract."
            return False, evidence

    evidence["reason"] = "Exact PPE contract verified: website-audit=$0.001 and synthetic events absent or zero."
    return True, evidence


def wait_run(run: dict, token: str, calls: int):
    run_id = run.get("id")
    status = run.get("status")
    polls = 0
    while run_id and status not in TERMINAL_RUN_STATUSES and polls < 4:
        path = f"/v2/actor-runs/{urllib.parse.quote(run_id, safe='')}?waitForFinish=60"
        http, payload = request_json("GET", path, token)
        calls += 1
        polls += 1
        if http != 200:
            return None, calls, polls, http
        run = payload.get("data") or {}
        status = run.get("status")
    # Completed-run cost/event aggregates are eventually consistent. Re-read after 10s.
    if run_id and status in TERMINAL_RUN_STATUSES:
        time.sleep(10)
        http, payload = request_json("GET", f"/v2/actor-runs/{urllib.parse.quote(run_id, safe='')}", token)
        calls += 1
        if http == 200:
            run = payload.get("data") or run
        else:
            return None, calls, polls, http
    return run, calls, polls, 200


def run_case(actor_id: str, token: str, input_payload: dict, calls: int):
    # One successful audit costs exactly $0.001 under the verified PPE contract.
    # This ceiling also prevents any accidental extra chargeable event from being accepted.
    path = (
        f"/v2/actors/{urllib.parse.quote(actor_id, safe='')}/runs"
        "?build=latest&memory=128&timeout=120&maxTotalChargeUsd=0.001&waitForFinish=60"
    )
    http, payload = request_json("POST", path, token, input_payload)
    calls += 1
    if http not in {200, 201}:
        return None, calls, http
    run = payload.get("data") or {}
    run, calls, _, http = wait_run(run, token, calls)
    return run, calls, http


def safe_run_summary(run: dict | None):
    if not run:
        return None
    return {
        "id": run.get("id"),
        "status": run.get("status"),
        "defaultDatasetId": run.get("defaultDatasetId"),
        "buildId": run.get("buildId"),
        "buildNumber": run.get("buildNumber"),
        "usage": run.get("usage"),
        "usageUsd": run.get("usageUsd"),
        "usageTotalUsd": run.get("usageTotalUsd"),
        "chargedEventCounts": run.get("chargedEventCounts"),
        "startedAt": run.get("startedAt"),
        "finishedAt": run.get("finishedAt"),
    }


def main() -> int:
    token = os.environ.get("APIFY_TOKEN", "").strip()
    execute = os.environ.get("APIFY_CLOUD_QA", "0") == "1"
    if not token:
        return emit({
            "status": "CONFIG_REQUIRED",
            "apify_token_configured": False,
            "qa_requested": execute,
            "network_calls_made": 0,
            "run_requests_made": 0,
            "message": "No APIFY_TOKEN was available. No Apify request was attempted.",
        })

    actor_ref = urllib.parse.quote(ACTOR_NAME, safe="")
    http, payload = request_json("GET", f"/v2/actors/{actor_ref}", token)
    calls = 1
    if http != 200:
        return emit({"status": "ACTOR_READ_FAILED", "http_status": http, "network_calls_made": calls, "run_requests_made": 0}, 1)
    actor = payload.get("data") or {}
    actor_id = actor.get("id")
    if not actor_id:
        return emit({"status": "ACTOR_ID_MISSING", "network_calls_made": calls, "run_requests_made": 0}, 2)
    if actor.get("isPublic") is not False:
        return emit({"status": "PRIVATE_ACTOR_GATE_BLOCKED", "network_calls_made": calls, "run_requests_made": 0, "actor_id": actor_id}, 3)

    pricing_ok, pricing = pricing_gate(actor)
    if not pricing_ok:
        return emit({
            "status": "PPE_GATE_BLOCKED",
            "network_calls_made": calls,
            "run_requests_made": 0,
            "actor_id": actor_id,
            "pricing": pricing,
        }, 4)

    if not execute:
        return emit({
            "status": "CLOUD_QA_PREFLIGHT_PASS",
            "network_calls_made": calls,
            "run_requests_made": 0,
            "actor_id": actor_id,
            "pricing": pricing,
        })

    cases = []

    valid, calls, http = run_case(actor_id, token, {"urls": ["https://example.com"]}, calls)
    if http != 200 or not valid:
        return emit({"status": "VALID_QA_RUN_START_OR_READ_FAILED", "http_status": http, "network_calls_made": calls, "run_requests_made": 1, "pricing": pricing}, 5)
    cases.append({"name": "valid_html", "run": safe_run_summary(valid)})

    valid_counts = valid.get("chargedEventCounts") or {}
    if valid.get("status") != "SUCCEEDED" or valid_counts.get(EXPECTED_EVENT) != 1:
        return emit({"status": "VALID_QA_CHARGE_BOUNDARY_FAILED", "network_calls_made": calls, "run_requests_made": 1, "pricing": pricing, "cases": cases}, 6)

    invalid, calls, http = run_case(actor_id, token, {"urls": ["http://127.0.0.1"]}, calls)
    if http != 200 or not invalid:
        return emit({"status": "INVALID_QA_RUN_START_OR_READ_FAILED", "http_status": http, "network_calls_made": calls, "run_requests_made": 2, "pricing": pricing, "cases": cases}, 7)
    cases.append({"name": "blocked_private_ip", "run": safe_run_summary(invalid)})

    invalid_counts = invalid.get("chargedEventCounts") or {}
    if invalid_counts.get(EXPECTED_EVENT, 0) != 0:
        return emit({"status": "INVALID_QA_WAS_CHARGED", "network_calls_made": calls, "run_requests_made": 2, "pricing": pricing, "cases": cases}, 8)

    valid_usage = dec(valid.get("usageTotalUsd")) or Decimal("0")
    invalid_usage = dec(invalid.get("usageTotalUsd")) or Decimal("0")
    observed_usage = valid_usage + invalid_usage
    revenue_per_1000 = EXPECTED_EVENT_PRICE * Decimal(1000)
    developer_share_before_cost = revenue_per_1000 * Decimal("0.8")

    return emit({
        "status": "CLOUD_QA_CORE_PASS",
        "network_calls_made": calls,
        "run_requests_made": 2,
        "actor_id": actor_id,
        "pricing": pricing,
        "cases": cases,
        "economics": {
            "customer_revenue_per_1000_successes_usd": float(revenue_per_1000),
            "developer_share_before_platform_cost_per_1000_usd": float(developer_share_before_cost),
            "observed_two_run_usage_total_usd": float(observed_usage),
            "note": "Per-1000 developer profit requires representative paid-plan usage measurement; this core QA only measures the two bounded owner runs."
        },
    })


if __name__ == "__main__":
    sys.exit(main())
