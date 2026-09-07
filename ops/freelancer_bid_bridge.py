#!/usr/bin/env python3
"""Fail-closed Freelancer.com bid bridge.

Uses the official Freelancer Python SDK. No browser automation, no scraped session
cookies, and no bid is submitted unless --submit is explicitly supplied.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass

from freelancersdk.exceptions import BidNotPlacedException
from freelancersdk.resources.projects import get_project_by_id, place_project_bid
from freelancersdk.resources.projects.helpers import (
    create_get_projects_project_details_object,
    create_get_projects_user_details_object,
)
from freelancersdk.resources.users import get_self_user_id
from freelancersdk.session import Session

DEFAULT_URL = "https://www.freelancer.com"


@dataclass
class BidSpec:
    project_id: int
    amount: float
    period: int
    milestone_percentage: int
    description: str


def require_token() -> str:
    token = os.environ.get("FLN_OAUTH_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "FLN_OAUTH_TOKEN is not set. Refusing all Freelancer API writes."
        )
    return token


def make_session() -> Session:
    return Session(
        oauth_token=require_token(),
        url=os.environ.get("FLN_URL", DEFAULT_URL).strip() or DEFAULT_URL,
    )


def verify_identity(session: Session) -> int:
    user_id = get_self_user_id(session)
    if not user_id:
        raise RuntimeError("Authenticated Freelancer identity could not be resolved.")
    return int(user_id)


def fetch_project(session: Session, project_id: int):
    project_details = create_get_projects_project_details_object(
        full_description=True,
        jobs=True,
    )
    user_details = create_get_projects_user_details_object(basic=True)
    return get_project_by_id(
        session,
        int(project_id),
        project_details=project_details,
        user_details=user_details,
    )


def submit_bid(session: Session, bidder_id: int, spec: BidSpec):
    try:
        return place_project_bid(
            session,
            project_id=spec.project_id,
            bidder_id=bidder_id,
            amount=spec.amount,
            period=spec.period,
            milestone_percentage=spec.milestone_percentage,
            description=spec.description,
        )
    except BidNotPlacedException as exc:
        message = getattr(exc, "message", str(exc))
        code = getattr(exc, "error_code", None)
        request_id = getattr(exc, "request_id", None)
        raise RuntimeError(
            f"Freelancer rejected bid: message={message!r} code={code!r} request_id={request_id!r}"
        ) from exc


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate and submit a Freelancer.com bid")
    p.add_argument("--project-id", type=int, required=True)
    p.add_argument("--amount", type=float, required=True)
    p.add_argument("--period", type=int, required=True, help="Delivery period in days")
    p.add_argument("--milestone-percentage", type=int, default=100)
    p.add_argument("--description-file", required=True)
    p.add_argument(
        "--submit",
        action="store_true",
        help="Actually place the bid. Without this flag the command is read-only.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not 0 <= args.milestone_percentage <= 100:
        raise ValueError("milestone percentage must be between 0 and 100")
    if args.amount <= 0 or args.period <= 0:
        raise ValueError("amount and period must be positive")

    description = open(args.description_file, "r", encoding="utf-8").read().strip()
    if not description:
        raise ValueError("bid description is empty")

    spec = BidSpec(
        project_id=args.project_id,
        amount=args.amount,
        period=args.period,
        milestone_percentage=args.milestone_percentage,
        description=description,
    )

    session = make_session()
    bidder_id = verify_identity(session)
    project = fetch_project(session, spec.project_id)

    print(json.dumps({
        "mode": "SUBMIT" if args.submit else "DRY_RUN",
        "bidder_id": bidder_id,
        "bid": asdict(spec),
        "project_found": bool(project),
    }, indent=2, default=str))

    if not args.submit:
        print("DRY_RUN_OK: authenticated identity and project were resolved; no bid placed.")
        return 0

    result = submit_bid(session, bidder_id, spec)
    print(json.dumps({"status": "BID_SUBMITTED", "result": result}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
