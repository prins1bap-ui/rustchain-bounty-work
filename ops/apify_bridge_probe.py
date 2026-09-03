# Probe trigger: 2026-09-03 monetization preflight recheck
import json
import os
import sys
import urllib.error
import urllib.request

BASE = "https://api.apify.com"
RESULT_PATH = "apify_bridge_result.json"


def write_result(payload):
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    print(json.dumps(payload, sort_keys=True))


def get_json(path, token):
    req = urllib.request.Request(
        BASE + path,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "apify-github-bridge/0.1",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Never print request headers or the token. Return only safe status metadata.
        return exc.code, {"error": {"type": "http_error", "status": exc.code}}
    except Exception as exc:
        return 0, {"error": {"type": exc.__class__.__name__}}


def main():
    token = os.environ.get("APIFY_TOKEN", "").strip()
    if not token:
        write_result({
            "status": "CONFIG_REQUIRED",
            "apify_token_configured": False,
            "network_calls_made": 0,
            "paid_actions_made": 0,
            "message": "APIFY_TOKEN repository secret is not configured. No Apify request was attempted.",
        })
        return 0

    endpoints = {
        "me": "/v2/users/me",
        "limits": "/v2/users/me/limits",
        "actors": "/v2/actors?my=1&limit=100&desc=1",
    }

    raw = {}
    statuses = {}
    for key, path in endpoints.items():
        status, payload = get_json(path, token)
        statuses[key] = status
        raw[key] = payload
        if status != 200:
            write_result({
                "status": "APIFY_READ_FAILED",
                "apify_token_configured": True,
                "http_statuses": statuses,
                "failed_endpoint": key,
                "paid_actions_made": 0,
            })
            return 1

    me = raw["me"].get("data", {})
    limits_data = raw["limits"].get("data", {})
    actors_data = raw["actors"].get("data", {})

    safe_actors = []
    for item in actors_data.get("items", []):
        safe_actors.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "title": item.get("title"),
            "username": item.get("username"),
            "createdAt": item.get("createdAt"),
            "modifiedAt": item.get("modifiedAt"),
        })

    safe_limits = {
        "monthlyUsageCycle": limits_data.get("monthlyUsageCycle"),
        "limits": limits_data.get("limits"),
        "current": limits_data.get("current"),
    }

    write_result({
        "status": "READ_ONLY_OK",
        "apify_token_configured": True,
        "paid_actions_made": 0,
        "http_statuses": statuses,
        "account": {
            "id": me.get("id"),
            "username": me.get("username"),
            "email": me.get("email"),
            "plan": me.get("plan"),
        },
        "limits": safe_limits,
        "owned_actor_count_returned": len(safe_actors),
        "actors": safe_actors,
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
