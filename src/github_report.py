"""GitHub API reporter for repository activity summaries."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


API_ROOT = "https://api.github.com"


@dataclass(frozen=True)
class RepoReport:
    full_name: str
    open_issues: int
    stars: int
    forks: int
    default_branch: str
    updated_at: str


def get_token() -> str | None:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def github_request(path: str, *, token: str | None = None) -> Any:
    url = f"{API_ROOT}{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "devops-python-devops-lab",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {exc.code}: {body}") from exc


def fetch_repo_report(owner: str, repo: str, *, token: str | None = None) -> RepoReport:
    data = github_request(f"/repos/{owner}/{repo}", token=token)
    return RepoReport(
        full_name=data["full_name"],
        open_issues=data.get("open_issues_count", 0),
        stars=data.get("stargazers_count", 0),
        forks=data.get("forks_count", 0),
        default_branch=data.get("default_branch", "main"),
        updated_at=data.get("updated_at", ""),
    )


def fetch_recent_commits(owner: str, repo: str, *, token: str | None = None, limit: int = 5) -> list[dict[str, str]]:
    data = github_request(f"/repos/{owner}/{repo}/commits?per_page={limit}", token=token)
    commits: list[dict[str, str]] = []
    for row in data:
        commit = row.get("commit", {})
        commits.append(
            {
                "sha": row.get("sha", "")[:7],
                "message": (commit.get("message") or "").splitlines()[0],
                "author": (commit.get("author") or {}).get("name", "unknown"),
                "date": (commit.get("author") or {}).get("date", ""),
            }
        )
    return commits


def build_report(owner: str, repo: str, *, token: str | None = None) -> dict[str, Any]:
    summary = fetch_repo_report(owner, repo, token=token)
    commits = fetch_recent_commits(owner, repo, token=token)
    return {
        "repository": summary.full_name,
        "default_branch": summary.default_branch,
        "open_issues": summary.open_issues,
        "stars": summary.stars,
        "forks": summary.forks,
        "updated_at": summary.updated_at,
        "recent_commits": commits,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate GitHub repository activity report")
    parser.add_argument("owner", help="GitHub org or user")
    parser.add_argument("repo", help="Repository name")
    parser.add_argument("--token-env", default="GITHUB_TOKEN", help="Env var for API token")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    token = os.environ.get(args.token_env) or get_token()

    try:
        report = build_report(args.owner, args.repo, token=token)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
