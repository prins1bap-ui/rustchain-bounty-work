from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

BASE = "https://api.apify.com"
RESULT_PATH = "apify_controlled_deploy_result.json"
ACTOR_NAME = "website-tech-contact-snapshot"
ACTOR_TITLE = "Website Contact + Tech Snapshot"
ACTOR_DESCRIPTION = (
    "One-request public website enrichment: contacts, social profiles, technology "
    "fingerprints, metadata, JSON-LD, forms, and security-header signals."
)
VERSION = "0.1"
GIT_REPO_URL = (
    "https://github.com/prins1bap-ui/rustchain-bounty-work"
    "#apify-bridge-20260902:apify_actor"
)


def emit(payload: dict, code: int = 0) -> int:
    payload.setdefault("actor_name", ACTOR_NAME)
    payload.setdefault("version", VERSION)
    payload.setdefault("unauthorized_spend_usd", 0)
    with open(RESULT_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
    print(json.dumps(payload, sort_keys=True))
    return code


def request_json(method: str, path: str, token: str, body: dict | None = None):
    data = None
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "apify-controlled-deploy/0.1",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        # Do not echo response bodies because third-party errors can unexpectedly contain
        # request material. Status and endpoint are sufficient for fail-closed diagnosis.
        return exc.code, {"error": {"type": "http_error", "status": exc.code}}
    except Exception as exc:  # pragma: no cover - defensive network boundary
        return 0, {"error": {"type": exc.__class__.__name__}}


def dec(value, default=None):
    try:
        if value is None:
            return default
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def plan_is_zero_overage_safe(me: dict, limits_payload: dict) -> tuple[bool, dict]:
    plan = me.get("plan") or {}
    limits = limits_payload.get("limits") or {}
    current = limits_payload.get("current") or {}

    plan_id = str(plan.get("id") or "").strip()
    base_price = dec(plan.get("monthlyBasePriceUsd"))
    prepaid = dec(plan.get("monthlyUsageCreditsUsd"))
    max_usage = dec(limits.get("maxMonthlyUsageUsd"))
    current_usage = dec(current.get("monthlyUsageUsd"))

    evidence = {
        "plan_id": plan_id or None,
        "monthly_base_price_usd": float(base_price) if base_price is not None else None,
        "monthly_prepaid_usage_credits_usd": float(prepaid) if prepaid is not None else None,
        "max_monthly_usage_usd": float(max_usage) if max_usage is not None else None,
        "current_monthly_usage_usd": float(current_usage) if current_usage is not None else None,
    }

    if not plan_id or base_price is None or prepaid is None or max_usage is None or current_usage is None:
        evidence["reason"] = "Required account-specific billing fields are missing."
        return False, evidence

    if current_usage > max_usage:
        evidence["reason"] = "Current usage exceeds the reported hard monthly limit; state is inconsistent."
        return False, evidence

    # Free accounts have no pay-as-you-go overage. Their services suspend when prepaid
    # credits are exhausted. Requiring a $0 base price and zero or positive prepaid credits
    # prevents treating a paid plan as Free based on its name alone.
    if base_price == 0 and plan_id.lower() == "free":
        evidence["reason"] = "Free plan confirmed; no pay-as-you-go monetary overage path."
        return True, evidence

    # On paid plans, no *additional* monetary charge can arise from platform usage only if
    # the hard monthly usage ceiling is no greater than prepaid monthly usage credits.
    if max_usage <= prepaid:
        evidence["reason"] = "Hard monthly usage limit is at or below prepaid usage credits."
        return True, evidence

    evidence["reason"] = (
        "Paid-plan hard monthly usage limit exceeds prepaid credits, so additional overage "
        "is possible. Deployment is blocked."
    )
    return False, evidence


def main() -> int:
    token = os.environ.get("APIFY_TOKEN", "").strip()
    deploy = os.environ.get("APIFY_DEPLOY", "0") == "1"

    if not token:
        return emit({
            "status": "CONFIG_REQUIRED",
            "apify_token_configured": False,
            "deploy_requested": deploy,
            "network_calls_made": 0,
            "paid_actions_made": 0,
            "message": "No APIFY_TOKEN was available. No Apify request was attempted.",
        })

    read_endpoints = {
        "me": "/v2/users/me",
        "limits": "/v2/users/me/limits",
        "usage": "/v2/users/me/usage/monthly",
        "actors": "/v2/actors?my=1&limit=100&desc=1",
    }
    raw = {}
    statuses = {}
    calls = 0
    for key, path in read_endpoints.items():
        status, payload = request_json("GET", path, token)
        calls += 1
        statuses[key] = status
        raw[key] = payload
        if status != 200:
            return emit({
                "status": "READ_GATE_FAILED",
                "apify_token_configured": True,
                "deploy_requested": deploy,
                "network_calls_made": calls,
                "paid_actions_made": 0,
                "failed_endpoint": key,
                "http_statuses": statuses,
            }, 1)

    me = raw["me"].get("data") or {}
    limits_data = raw["limits"].get("data") or {}
    actors_data = raw["actors"].get("data") or {}
    usage_data = raw["usage"].get("data") or {}

    safe, billing = plan_is_zero_overage_safe(me, limits_data)
    items = actors_data.get("items") or []
    matches = [item for item in items if item.get("name") == ACTOR_NAME]

    inventory = {
        "owned_actor_count_returned": len(items),
        "matching_actor_count": len(matches),
        "matching_actors": [
            {"id": item.get("id"), "name": item.get("name"), "title": item.get("title")}
            for item in matches
        ],
    }

    gate = {
        "account_username": me.get("username"),
        "billing": billing,
        "monthly_usage_total_after_volume_discount_usd": usage_data.get(
            "totalUsageCreditsUsdAfterVolumeDiscount"
        ),
        "inventory": inventory,
    }

    if not safe:
        return emit({
            "status": "ZERO_SPEND_GATE_BLOCKED",
            "apify_token_configured": True,
            "deploy_requested": deploy,
            "network_calls_made": calls,
            "paid_actions_made": 0,
            "gate": gate,
        }, 2)

    if len(matches) > 1:
        return emit({
            "status": "DUPLICATE_ACTOR_BLOCKED",
            "apify_token_configured": True,
            "deploy_requested": deploy,
            "network_calls_made": calls,
            "paid_actions_made": 0,
            "gate": gate,
        }, 3)

    if not deploy:
        return emit({
            "status": "READ_ONLY_GATE_PASS",
            "apify_token_configured": True,
            "deploy_requested": False,
            "network_calls_made": calls,
            "paid_actions_made": 0,
            "gate": gate,
        })

    # Only after account-specific zero-overage proof and duplicate prevention do writes begin.
    if matches:
        actor_id = matches[0].get("id")
        if not actor_id:
            return emit({
                "status": "ACTOR_ID_MISSING",
                "network_calls_made": calls,
                "paid_actions_made": 0,
                "gate": gate,
            }, 4)
        version_path = f"/v2/actors/{urllib.parse.quote(actor_id, safe='')}/versions/{VERSION}"
        version_body = {
            "versionNumber": VERSION,
            "sourceType": "GIT_REPO",
            "gitRepoUrl": GIT_REPO_URL,
        }
        status, _ = request_json("PUT", version_path, token, version_body)
        calls += 1
        if status not in {200, 201}:
            # Version may not exist yet; create it explicitly.
            create_version_path = f"/v2/actors/{urllib.parse.quote(actor_id, safe='')}/versions"
            status, _ = request_json("POST", create_version_path, token, version_body)
            calls += 1
            if status not in {200, 201}:
                return emit({
                    "status": "VERSION_WRITE_FAILED",
                    "network_calls_made": calls,
                    "paid_actions_made": 0,
                    "http_status": status,
                    "gate": gate,
                }, 5)
        actor_action = "UPDATED_EXISTING"
    else:
        create_body = {
            "name": ACTOR_NAME,
            "title": ACTOR_TITLE,
            "description": ACTOR_DESCRIPTION,
            "versions": [{
                "versionNumber": VERSION,
                "sourceType": "GIT_REPO",
                "gitRepoUrl": GIT_REPO_URL,
            }],
        }
        status, payload = request_json("POST", "/v2/actors", token, create_body)
        calls += 1
        if status not in {200, 201}:
            return emit({
                "status": "ACTOR_CREATE_FAILED",
                "network_calls_made": calls,
                "paid_actions_made": 0,
                "http_status": status,
                "gate": gate,
            }, 6)
        actor_id = (payload.get("data") or {}).get("id")
        if not actor_id:
            return emit({
                "status": "ACTOR_CREATE_RESPONSE_MISSING_ID",
                "network_calls_made": calls,
                "paid_actions_made": 0,
                "gate": gate,
            }, 7)
        actor_action = "CREATED_EXACTLY_ONE"

    # Actor builds consume platform usage credits. This request is permitted only because
    # the gate above proved there is no path to an *additional monetary* overage.
    build_path = (
        f"/v2/actors/{urllib.parse.quote(actor_id, safe='')}/builds"
        f"?version={urllib.parse.quote(VERSION)}&tag=latest&waitForFinish=60"
    )
    status, payload = request_json("POST", build_path, token, {})
    calls += 1
    if status not in {200, 201}:
        return emit({
            "status": "BUILD_START_FAILED",
            "network_calls_made": calls,
            "paid_actions_made": 1,
            "http_status": status,
            "actor_id": actor_id,
            "actor_action": actor_action,
            "gate": gate,
        }, 8)

    build = payload.get("data") or {}
    build_status = build.get("status")
    result_status = "PRIVATE_BUILD_SUCCEEDED" if build_status == "SUCCEEDED" else "PRIVATE_BUILD_STARTED_OR_INCOMPLETE"
    return emit({
        "status": result_status,
        "apify_token_configured": True,
        "deploy_requested": True,
        "network_calls_made": calls,
        "paid_actions_made": 1,
        "actor_id": actor_id,
        "actor_action": actor_action,
        "build": {
            "id": build.get("id"),
            "status": build_status,
            "startedAt": build.get("startedAt"),
            "finishedAt": build.get("finishedAt"),
        },
        "gate": gate,
    }, 0 if build_status == "SUCCEEDED" else 9)


if __name__ == "__main__":
    sys.exit(main())
