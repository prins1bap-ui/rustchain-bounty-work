from __future__ import annotations

import json
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .core import Check


class GitHubAPI:
    def __init__(self, token: str, target_owner: str = "Scottcjn") -> None:
        self.token = token
        self.target_owner = target_owner
        self.base = "https://api.github.com"

    def _request(self, path: str):
        req = Request(
            self.base + path,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "rtc-bounty-verifier/1.0",
            },
        )
        return urlopen(req, timeout=15)

    def follows_target(self, claimant: str) -> Check:
        path = f"/users/{quote(claimant)}/following/{quote(self.target_owner)}"
        try:
            with self._request(path) as r:
                return Check("pass", "follows target") if r.status == 204 else Check("unknown", f"unexpected status {r.status}")
        except HTTPError as exc:
            if exc.code == 404:
                return Check("fail", "does not follow target")
            return Check("unknown", f"GitHub API HTTP {exc.code}")
        except Exception as exc:
            return Check("unknown", f"GitHub API failed: {type(exc).__name__}")

    def count_owner_stars(self, claimant: str) -> Check:
        page = 1
        count = 0
        try:
            while True:
                path = f"/users/{quote(claimant)}/starred?per_page=100&page={page}"
                with self._request(path) as r:
                    items = json.load(r)
                if not isinstance(items, list):
                    return Check("unknown", "unexpected starred-repos response")
                count += sum(1 for repo in items if str(repo.get("owner", {}).get("login", "")).lower() == self.target_owner.lower())
                if len(items) < 100:
                    break
                page += 1
                if page > 100:
                    return Check("unknown", "pagination safety limit reached")
            return Check("pass", f"{count} repositories owned by {self.target_owner} starred")
        except HTTPError as exc:
            return Check("unknown", f"GitHub API HTTP {exc.code}")
        except Exception as exc:
            return Check("unknown", f"GitHub API failed: {type(exc).__name__}")

    def issue_comments(self, repo: str, issue: int) -> list[str]:
        owner, name = repo.split("/", 1)
        page = 1
        out: list[str] = []
        while True:
            path = f"/repos/{quote(owner)}/{quote(name)}/issues/{issue}/comments?per_page=100&page={page}"
            with self._request(path) as r:
                items = json.load(r)
            out.extend(str(item.get("body", "")) for item in items)
            if len(items) < 100:
                return out
            page += 1
