from datetime import datetime, timedelta, timezone

now = datetime(2026, 9, 2, tzinfo=timezone.utc)
window_start = now - timedelta(days=7)

claim = {
    "created_at": now - timedelta(days=8),
    "verified_at": now - timedelta(days=1),
    "rtc": 10.0,
}

included_by_current_query = claim["created_at"] > window_start
should_count_for_weekly_earnings = claim["verified_at"] > window_start

print("window_start:", window_start.isoformat())
print("claim_created:", claim["created_at"].isoformat())
print("claim_verified:", claim["verified_at"].isoformat())
print("included_by_created_filter:", included_by_current_query)
print("should_count_by_verification_time:", should_count_for_weekly_earnings)

assert included_by_current_query is False
assert should_count_for_weekly_earnings is True
print("REPRODUCED: current created-date query omits RTC verified inside the rolling 7-day window")
