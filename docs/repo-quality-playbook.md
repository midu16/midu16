# Repository quality playbook

This document targets the **Repository Quality** dimension on [GitScore](https://gitscore.live/) (250 points). A score around 144/250 usually means the portfolio is active but diluted: many public forks, low aggregate stars, and missing metadata on original repositories.

## Current profile signals (midu16)

| Signal | Typical value | Why it matters |
|--------|---------------|----------------|
| Public repositories | ~200+ | Large portfolios dilute average quality unless originals stand out |
| Original vs fork ratio | ~90 / ~116 | Forks count toward volume but rarely toward “quality” signals |
| Stars on original repos | low (max ~2) | GitScore rewards repos others star and fork |
| Missing license (original) | ~50 | No `LICENSE` file → GitHub reports no license |
| Missing topics (original) | ~80+ | Topics improve discoverability and scoring heuristics |
| Missing description | ~28 | Empty descriptions look unmaintained |

## Highest-impact actions

### 1. Curate the public portfolio

- **Pin six repositories** on your GitHub profile: `l1-cp`, `prega-release-notes`, `lemonade`, and three other active originals.
- **Archive forks** you are not actively contributing to (Settings → Archive). This does not delete work; it removes noise from your public portfolio.
- **Avoid publishing** empty or duplicate repos (numeric course IDs, one-file experiments). Make them private or archive them.

### 2. Fix metadata on active originals

For each repo you keep public:

1. Add a root **`LICENSE`** file (Apache-2.0 or MIT are fine for personal tooling).
2. Set a one-line **description** on GitHub.
3. Add **topics** (3–6 relevant tags).
4. Keep a short **README** with purpose, prerequisites, and one working example.

Use the bundled metadata map:

```bash
cd ~/midu16
DRY_RUN=1 ./scripts/repo-hygiene.sh   # preview
./scripts/repo-hygiene.sh             # apply via gh CLI
```

### 3. Maintain a small set of “flagship” repos

GitScore rewards repositories that receive stars and forks over time. Invest polish in a handful of originals instead of spreading thin across 90 public repos.

Suggested flagships:

| Repository | Focus |
|------------|-------|
| [l1-cp](https://github.com/midu16/l1-cp) | OpenShift telco hub/spoke lab |
| [prega-release-notes](https://github.com/midu16/prega-release-notes) | OLM release-notes tooling |
| [lemonade](https://github.com/midu16/lemonade) | Upstream contributions to Lemonade SDK |

### 4. Run the analyzer regularly

```bash
python3 scripts/analyze_github_profile.py midu16 \
  --json-out /tmp/profile-report.json \
  --markdown-out docs/repo-quality-report.md
```

The GitHub Action [repo-analysis.yml](../.github/workflows/repo-analysis.yml) runs this on a schedule and updates the profile README metrics section.

## What will not move the score quickly

- Cosmetic README badges alone
- Duplicating troubleshooting text across many repos
- Keeping 100+ inactive public forks visible

Stars and downstream forks require real utility. Metadata and curation make your best work visible; the playbook above aligns the portfolio with that goal.
