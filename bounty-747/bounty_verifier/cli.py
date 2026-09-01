from __future__ import annotations

import argparse
import os
import sys

from .core import Check, Verification, article_word_count, duplicate_payment_check, extract_article_url, extract_wallet, markdown
from .github_api import GitHubAPI
from .node_api import NodeAPI


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--issue", required=True, type=int)
    p.add_argument("--claimant", required=True)
    p.add_argument("--claim-text", required=True)
    args = p.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    node_url = os.environ.get("RUSTCHAIN_NODE_URL")
    target = os.environ.get("TARGET_OWNER", "Scottcjn")
    if not token or not node_url:
        print("GITHUB_TOKEN and RUSTCHAIN_NODE_URL are required", file=sys.stderr)
        return 2

    gh = GitHubAPI(token, target)
    wallet = extract_wallet(args.claim_text)
    article_url = extract_article_url(args.claim_text)

    follows = gh.follows_target(args.claimant)
    stars = gh.count_owner_stars(args.claimant)
    wallet_check = NodeAPI(node_url).wallet_exists(wallet) if wallet else Check("fail", "no native RTC wallet found in claim")
    article_check = article_word_count(article_url) if article_url else Check("n/a", "no supported article URL found in claim")
    try:
        comments = gh.issue_comments(args.repo, args.issue)
        duplicate = duplicate_payment_check(comments, args.claimant)
    except Exception as exc:
        duplicate = Check("unknown", f"history query failed: {type(exc).__name__}")

    result = Verification(args.claimant, follows, stars, wallet_check, article_check, duplicate)
    print(markdown(result))
    print("\n```json")
    print(result.json())
    print("```")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
