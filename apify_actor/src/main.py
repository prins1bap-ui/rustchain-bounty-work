from __future__ import annotations

import asyncio

from apify import Actor

from .scanner import audit_url, deduplicate_urls

MAX_URLS_PER_RUN = 500
CHARGED_EVENT = "website-audit"


async def main() -> None:
    async with Actor:
        actor_input = await Actor.get_input() or {}
        raw_urls = actor_input.get("urls") or []
        timeout_seconds = float(actor_input.get("timeoutSeconds", 10))
        max_retries = int(actor_input.get("maxRetries", 1))

        if not isinstance(raw_urls, list):
            raw_urls = []

        urls, duplicate_count = deduplicate_urls(raw_urls[:MAX_URLS_PER_RUN])
        Actor.log.info(
            "Processing %d unique URL(s); removed %d duplicate(s).",
            len(urls),
            duplicate_count,
        )

        success_count = 0
        error_count = 0
        for raw_url in urls:
            result = await asyncio.to_thread(
                audit_url,
                raw_url,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
            )
            if result["status"] == "SUCCESS":
                charge_result = await Actor.push_data(result, charged_event_name=CHARGED_EVENT)
                # `push_data(..., charged_event_name=...)` only writes items that fit
                # within the user's PPE budget. Count what was actually written/charged,
                # including the boundary case where this item consumes the last allowed
                # charge and `event_charge_limit_reached` becomes true immediately after.
                success_count += charge_result.charged_count if charge_result is not None else 1
                if charge_result and charge_result.event_charge_limit_reached:
                    Actor.log.info("User spending limit reached; stopping before additional work.")
                    break
            else:
                # Error records are intentionally uncharged. Pricing must use only the
                # custom `website-audit` event, with synthetic dataset-item billing removed.
                await Actor.push_data(result)
                error_count += 1

        Actor.log.info("Completed: %d successful audit(s), %d error record(s).", success_count, error_count)
