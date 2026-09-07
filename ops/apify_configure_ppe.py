from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

BASE = "https://api.apify.com"
ACTOR_NAME = "website-tech-contact-snapshot"
RESULT_PATH = "apify_configure_ppe_result.json"
EXPECTED_EVENT = "website-audit"
EXPECTED_PRICE = Decimal("0.001")
PAYOUT_BLOCKER = "cannot-monetize-without-payout-billing-info"


def emit(payload: dict, code: int = 0) -> int:
    payload.setdefault("actor_name", ACTOR_NAME)
    payload.setdefault("unauthorized_spend_usd", 0)
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    print(json.dumps(payload, sort_keys=True))
    return code


def request_json(method: str, path: str, token: str, body=None):
    data = None
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}", "User-Agent": "apify-ppe-config/0.2"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=70) as r:
            raw = r.read().decode("utf-8")
            return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {}
        except Exception:
            payload = {}
        err = payload.get("error") if isinstance(payload, dict) else None
        safe = {"error": {"type": (err or {}).get("type"), "status": exc.code}}
        return exc.code, safe
    except Exception as exc:
        return 0, {"error": {"type": exc.__class__.__name__, "status": 0}}


def dec(value):
    try:
        return Decimal(str(value)) if value is not None else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def main() -> int:
    token = os.environ.get("APIFY_TOKEN", "").strip()
    if not token:
        return emit({"status": "CONFIG_REQUIRED", "network_calls_made": 0, "message": "No APIFY_TOKEN available; no Apify request attempted."})

    calls = 0
    http, mep = request_json("GET", "/v2/users/me", token); calls += 1
    if http != 200:
        return emit({"status": "ACCOUNT_READ_FAILED", "http_status": http, "network_calls_made": calls}, 1)
    me = mep.get("data") or {}
    plan = me.get("plan") or {}

    http, limp = request_json("GET", "/v2/users/me/limits", token); calls += 1
    if http != 200:
        return emit({"status": "LIMITS_READ_FAILED", "http_status": http, "network_calls_made": calls}, 2)
    limits_payload = limp.get("data") or {}
    limits = limits_payload.get("limits") or {}
    current = limits_payload.get("current") or {}
    max_usage = dec(limits.get("maxMonthlyUsageUsd"))
    current_usage = dec(current.get("monthlyUsageUsd"))
    base = dec(plan.get("monthlyBasePriceUsd"))
    credits = dec(plan.get("monthlyUsageCreditsUsd"))
    plan_id = str(plan.get("id") or "").upper()
    billing = {"plan_id": plan_id, "monthly_base_price_usd": float(base) if base is not None else None,
               "monthly_prepaid_usage_credits_usd": float(credits) if credits is not None else None,
               "max_monthly_usage_usd": float(max_usage) if max_usage is not None else None,
               "current_monthly_usage_usd": float(current_usage) if current_usage is not None else None}

    if not (plan_id == "FREE" and base == 0 and max_usage is not None and current_usage is not None and current_usage <= max_usage):
        return emit({"status": "ZERO_OVERAGE_GATE_BLOCKED", "network_calls_made": calls, "billing": billing}, 3)

    http, invp = request_json("GET", "/v2/actors?my=1&limit=100&desc=1", token); calls += 1
    if http != 200:
        return emit({"status": "ACTOR_INVENTORY_FAILED", "http_status": http, "network_calls_made": calls, "billing": billing}, 4)
    actors = ((invp.get("data") or {}).get("items") or [])
    matches = [a for a in actors if a.get("name") == ACTOR_NAME]
    if len(matches) != 1:
        return emit({"status": "ACTOR_CARDINALITY_BLOCKED", "matching_actor_count": len(matches), "network_calls_made": calls, "billing": billing}, 5)
    actor_id = matches[0].get("id")

    http, actp = request_json("GET", f"/v2/actors/{urllib.parse.quote(actor_id, safe='')}", token); calls += 1
    if http != 200:
        return emit({"status": "ACTOR_READ_FAILED", "http_status": http, "network_calls_made": calls, "billing": billing}, 6)
    actor = actp.get("data") or {}
    if actor.get("isPublic") is not False:
        return emit({"status": "PRIVATE_ACTOR_GATE_BLOCKED", "actor_id": actor_id, "network_calls_made": calls, "billing": billing}, 7)

    infos = actor.get("pricingInfos") or []
    if infos:
        return emit({"status": "PRICING_ALREADY_PRESENT_NO_CHANGE", "actor_id": actor_id, "network_calls_made": calls, "billing": billing,
                     "pricing_models": [x.get("pricingModel") for x in infos]})

    body = {
        "pricingInfos": [{
            "pricingModel": "PAY_PER_EVENT",
            "pricingPerEvent": {
                "actorChargeEvents": {
                    EXPECTED_EVENT: {
                        "eventTitle": "Successful website audit",
                        "eventDescription": "Charged once for each unique URL that returns a successful HTML audit result.",
                        "eventPriceUsd": float(EXPECTED_PRICE),
                        "isPrimaryEvent": True,
                        "isOneTimeEvent": False
                    }
                }
            },
            "minimalMaxTotalChargeUsd": float(EXPECTED_PRICE)
        }]
    }
    http, upp = request_json("PUT", f"/v2/actors/{urllib.parse.quote(actor_id, safe='')}", token, body); calls += 1
    if http not in {200, 201}:
        err = (upp.get("error") or {}).get("type")
        if err == PAYOUT_BLOCKER:
            return emit({
                "status": "PAYOUT_BILLING_INFO_REQUIRED",
                "actor_id": actor_id,
                "http_status": http,
                "error_type": err,
                "network_calls_made": calls,
                "billing": billing,
                "legal_or_payment_action_attempted": False,
                "message": "Apify refuses monetization until payout billing details are completed. No billing, payout, KYC, legal, or payment-setting change was attempted."
            }, 12)
        return emit({"status": "PPE_CONFIGURATION_BLOCKED", "actor_id": actor_id, "http_status": http,
                     "error_type": err, "network_calls_made": calls, "billing": billing,
                     "legal_or_payment_action_attempted": False}, 8)

    updated = upp.get("data") or {}
    if updated.get("isPublic") is not False:
        return emit({"status": "PRIVACY_REGRESSION_BLOCKED", "actor_id": actor_id, "network_calls_made": calls, "billing": billing}, 9)

    http, verify_p = request_json("GET", f"/v2/actors/{urllib.parse.quote(actor_id, safe='')}", token); calls += 1
    if http != 200:
        return emit({"status": "PPE_VERIFY_READ_FAILED", "actor_id": actor_id, "http_status": http, "network_calls_made": calls, "billing": billing}, 10)
    verify = verify_p.get("data") or {}
    infos = verify.get("pricingInfos") or []
    return emit({"status": "PPE_CONFIGURATION_ATTEMPT_APPLIED", "actor_id": actor_id, "network_calls_made": calls, "billing": billing,
                 "pricing_models": [x.get("pricingModel") for x in infos], "is_public": verify.get("isPublic")})


if __name__ == "__main__":
    sys.exit(main())
