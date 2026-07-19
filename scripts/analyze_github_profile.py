#!/usr/bin/env python3
"""Analyze a GitHub user's public repositories and estimate GitScore-style quality."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any


def parse_iso8601(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def fetch_all_repos(username: str, token: str | None) -> list[dict[str, Any]]:
    repos: list[dict[str, Any]] = []
    page = 1
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "midu16-profile-analyzer",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    while True:
        url = (
            f"https://api.github.com/users/{username}/repos"
            f"?per_page=100&page={page}&type=public&sort=pushed"
        )
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                batch = json.load(response)
        except urllib.error.HTTPError as exc:
            raise SystemExit(f"GitHub API error on page {page}: {exc}") from exc

        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    return repos


def estimate_gitscore_repo_quality(repos: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    six_months_ago = now - timedelta(days=183)
    three_months_ago = now - timedelta(days=92)

    originals = [r for r in repos if not r.get("fork") and not r.get("archived")]
    forks = [r for r in repos if r.get("fork") and not r.get("archived")]
    archived = [r for r in repos if r.get("archived")]

    total_stars = sum(int(r.get("stargazers_count") or 0) for r in repos)
    total_forks_received = sum(int(r.get("forks_count") or 0) for r in originals)

    metadata_gaps: list[dict[str, str]] = []
    quality_points = 0.0
    max_quality_points = max(len(originals), 1) * 8.0

    for repo in originals:
        repo_points = 0.0
        name = repo["name"]
        gaps: list[str] = []

        stars = int(repo.get("stargazers_count") or 0)
        forks_count = int(repo.get("forks_count") or 0)
        if stars > 0:
            repo_points += min(stars, 5) * 0.5
        if forks_count > 0:
            repo_points += min(forks_count, 5) * 0.5

        if repo.get("description"):
            repo_points += 1.0
        else:
            gaps.append("description")

        if repo.get("license"):
            repo_points += 2.0
        else:
            gaps.append("license")

        topics = repo.get("topics") or []
        if topics:
            repo_points += 1.0
        else:
            gaps.append("topics")

        pushed_at = repo.get("pushed_at")
        if pushed_at and parse_iso8601(pushed_at) >= six_months_ago:
            repo_points += 2.0
        elif pushed_at and parse_iso8601(pushed_at) >= three_months_ago:
            repo_points += 1.0

        quality_points += min(repo_points, 8.0)
        if gaps:
            metadata_gaps.append({"name": name, "gaps": ", ".join(gaps)})

    portfolio_ratio = len(originals) / max(len(repos), 1)
    star_component = min(total_stars / 50.0, 1.0) * 70.0
    fork_component = min(total_forks_received / 20.0, 1.0) * 40.0
    metadata_component = (quality_points / max_quality_points) * 90.0
    portfolio_component = portfolio_ratio * 50.0

    estimated_score = min(
        250.0,
        star_component + fork_component + metadata_component + portfolio_component,
    )

    active_originals = sum(
        1
        for repo in originals
        if repo.get("pushed_at")
        and parse_iso8601(repo["pushed_at"]) >= six_months_ago
    )

    top_originals = sorted(
        originals,
        key=lambda repo: (
            int(repo.get("stargazers_count") or 0),
            int(repo.get("forks_count") or 0),
            repo.get("pushed_at") or "",
        ),
        reverse=True,
    )[:10]

    return {
        "username": repos[0]["owner"]["login"] if repos else "",
        "total_repos": len(repos),
        "original_repos": len(originals),
        "fork_repos": len(forks),
        "archived_repos": len(archived),
        "active_original_repos_6mo": active_originals,
        "total_stars": total_stars,
        "total_forks_received": total_forks_received,
        "originals_without_license": sum(1 for r in originals if not r.get("license")),
        "originals_without_topics": sum(1 for r in originals if not (r.get("topics") or [])),
        "originals_without_description": sum(
            1 for r in originals if not r.get("description")
        ),
        "estimated_gitscore_repo_quality": round(estimated_score),
        "estimated_gitscore_max": 250,
        "top_original_repos": [
            {
                "name": repo["name"],
                "stars": int(repo.get("stargazers_count") or 0),
                "forks": int(repo.get("forks_count") or 0),
                "license": (repo.get("license") or {}).get("spdx_id"),
                "topics": repo.get("topics") or [],
            }
            for repo in top_originals
        ],
        "metadata_gaps": sorted(
            metadata_gaps,
            key=lambda item: len(item["gaps"].split(", ")),
            reverse=True,
        )[:25],
        "analyzed_at": now.strftime("%Y-%m-%d"),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Repository quality report",
        "",
        f"Generated for `{report['username']}` on {report['analyzed_at']}.",
        "",
        "## GitScore estimate",
        "",
        f"- **Repository quality (estimated):** {report['estimated_gitscore_repo_quality']}/{report['estimated_gitscore_max']}",
        f"- **Public repositories:** {report['total_repos']} "
        f"({report['original_repos']} original, {report['fork_repos']} forks, "
        f"{report['archived_repos']} archived)",
        f"- **Stars received:** {report['total_stars']}",
        f"- **Forks received on original repos:** {report['total_forks_received']}",
        f"- **Active original repos (6 months):** {report['active_original_repos_6mo']}",
        "",
        "## Metadata gaps on original repos",
        "",
        f"- Missing license: {report['originals_without_license']}",
        f"- Missing topics: {report['originals_without_topics']}",
        f"- Missing description: {report['originals_without_description']}",
        "",
        "## Top original repositories",
        "",
        "| Repository | Stars | Forks | License | Topics |",
        "|------------|------:|------:|---------|--------|",
    ]

    for repo in report["top_original_repos"]:
        license_value = repo["license"] or "none"
        topics_value = ", ".join(repo["topics"]) if repo["topics"] else "none"
        lines.append(
            f"| [{repo['name']}](https://github.com/{report['username']}/{repo['name']}) "
            f"| {repo['stars']} | {repo['forks']} | {license_value} | {topics_value} |"
        )

    if report["metadata_gaps"]:
        lines.extend(
            [
                "",
                "## Highest-impact fixes",
                "",
                "| Repository | Missing |",
                "|------------|---------|",
            ]
        )
        for item in report["metadata_gaps"]:
            lines.append(f"| {item['name']} | {item['gaps']} |")

    lines.extend(
        [
            "",
            "## Recommended actions",
            "",
            "1. Pin your six strongest original repositories on your GitHub profile.",
            "2. Archive inactive forks you are not contributing to.",
            "3. Add a `LICENSE` file, description, and topics to active original repos.",
            "4. Keep one concise README per repo; avoid duplicating the same note across many forks.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("username", nargs="?", default="midu16")
    parser.add_argument(
        "--json-out",
        default="",
        help="Write machine-readable report to this path.",
    )
    parser.add_argument(
        "--markdown-out",
        default="",
        help="Write markdown report to this path.",
    )
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    repos = fetch_all_repos(args.username, token)
    report = estimate_gitscore_repo_quality(repos)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
            handle.write("\n")

    if args.markdown_out:
        with open(args.markdown_out, "w", encoding="utf-8") as handle:
            handle.write(render_markdown(report))

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
