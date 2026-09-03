from __future__ import annotations

import asyncio
from decimal import Decimal, InvalidOperation

from apify import Actor

from .public_transport import public_client_factory
from .scanner import audit_url, deduplicate_urls

MAX_URLS_PER_RUN = 500
CHARGED_EVENT = "website-audit"
EXPECTED_EVENT_PRICE_USD = Decimal("0.001")
ERROR_DATASET_ALIAS = "errors"
SYNTHETIC_EVENTS_THAT_MUST_NOT_CHARGE = (
    "apify-default-dataset-item",
    "apify-actor-start",
)


def _decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _pricing_event_prices(pricing_info: object) -> dict[str, Decimal | None]:
    """Return flat event prices across supported Apify SDK pricing-info shapes."""
    direct_prices = getattr(pricing_info, "per_event_prices", None)
    if isinstance(direct_prices, dict):
        return {str(name): _decimal(price) for name, price in direct_prices.items()}

    pricing_per_event = getattr(pricing_info, "pricing_per_event", None)
    events = getattr(pricing_per_event, "actor_charge_events", None)
    if isinstance(events, dict):
        return {
            str(name): _decimal(getattr(event, "event_price_usd", None))
            for name, event in events.items()
        }
    return {}


def _is_pay_per_event(pricing_info: object) -> bool:
    explicit = getattr(pricing_info, "is_pay_per_event", None)
    if explicit is not None:
        return bool(explicit)
    pricing_model = getattr(pricing_info, "pricing_model", None)
    value = getattr(pricing_model, "value", pricing_model)
    return str(value).upper() == "PAY_PER_EVENT"


def _assert_safe_pricing_configuration() -> None:
    """Fail closed if production PPE pricing can bill anything except a successful audit."""
    pricing_info = Actor.get_charging_manager().get_pricing_info()
    if not _is_pay_per_event(pricing_info):
        return

    prices = _pricing_event_prices(pricing_info)
    website_audit_price = prices.get(CHARGED_EVENT)
    if website_audit_price != EXPECTED_EVENT_PRICE_USD:
        raise RuntimeError(
            "Unsafe PPE configuration: website-audit must be priced at exactly $0.001 before this Actor runs."
        )

    for event_name in SYNTHETIC_EVENTS_THAT_MUST_NOT_CHARGE:
        price = prices.get(event_name)
        if price is not None and price != Decimal("0"):
            raise RuntimeError(
                f"Unsafe PPE configuration: {event_name} must be removed or non-billable before this Actor runs."
            )


def _require_declared_html_content_type(result: dict) -> dict:
    """Never charge a response whose server did not actually declare an HTML content type.

    The scanner can parse a body when Content-Type is absent, but billing is intentionally
    stricter than parsing. A missing type is ambiguous (it can be HTML or arbitrary binary
    content), so the Actor fails closed and routes it to the uncharged error dataset.
    """
    if result.get("status") != "SUCCESS" or result.get("contentType"):
        return result

    safe = dict(result)
    safe.update(
        {
            "status": "ERROR",
            "errorCode": "UNVERIFIED_CONTENT_TYPE",
            "errorMessage": "Response omitted Content-Type, so HTML could not be verified safely",
            "title": None,
            "metaDescription": None,
            "generator": None,
            "language": None,
            "canonicalUrl": None,
            "organizationName": None,
            "structuredDataTypes": [],
            "detectedTechnologies": [],
            "forms": 0,
            "emails": [],
            "phones": [],
            "socialProfiles": {},
        }
    )
    return safe


async def main() -> None:
    async with Actor:
        # The Store promise is one custom charge per successful audit and zero
        # charges for invalid/failed targets. Fail closed if platform pricing
        # drifts from that contract.
        _assert_safe_pricing_configuration()

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
        error_dataset = None
        for raw_url in urls:
            result = await asyncio.to_thread(
                audit_url,
                raw_url,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                client_factory=public_client_factory,
            )
            result = _require_declared_html_content_type(result)
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
                # Only the default dataset can trigger Apify's synthetic
                # `apify-default-dataset-item` event. Error records are therefore stored
                # in a run-scoped aliased dataset, making them non-billable through that
                # synthetic event even if platform pricing is later misconfigured.
                if error_dataset is None:
                    error_dataset = await Actor.open_dataset(alias=ERROR_DATASET_ALIAS)
                await error_dataset.push_data(result)
                error_count += 1

        Actor.log.info("Completed: %d successful audit(s), %d error record(s).", success_count, error_count)
