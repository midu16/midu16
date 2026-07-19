#!/usr/bin/env bash
# Apply GitHub metadata (topics, descriptions) from metadata/repo-metadata.json.
# Requires: gh auth login (scopes: repo, read:user)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
METADATA="${ROOT}/metadata/repo-metadata.json"
OWNER="${GITHUB_OWNER:-midu16}"
DRY_RUN="${DRY_RUN:-0}"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required. Install it and run: gh auth login" >&2
  exit 1
fi

if [[ ! -f "${METADATA}" ]]; then
  echo "Missing ${METADATA}" >&2
  exit 1
fi

apply_repo() {
  local repo="$1"
  local description="$2"
  local topics_csv="$3"

  echo "==> ${OWNER}/${repo}"

  if [[ "${DRY_RUN}" == "1" ]]; then
    echo "  description: ${description}"
    echo "  topics: ${topics_csv}"
    return 0
  fi

  if [[ -n "${description}" ]]; then
    gh repo edit "${OWNER}/${repo}" --description "${description}"
  fi

  if [[ -n "${topics_csv}" ]]; then
    topics_json="$(jq -cn --arg csv "${topics_csv}" '$csv | split(",")')"
    gh api -X PUT "repos/${OWNER}/${repo}/topics" \
      --input - <<< "{\"names\": ${topics_json}}" \
      -H "Accept: application/vnd.github.mercy-preview+json"
  fi
}

repo_count="$(jq '.repos | length' "${METADATA}")"
for ((i = 0; i < repo_count; i++)); do
  name="$(jq -r ".repos[$i].name" "${METADATA}")"
  description="$(jq -r ".repos[$i].description // \"\"" "${METADATA}")"
  topics="$(jq -r ".repos[$i].topics | join(\",\")" "${METADATA}")"
  apply_repo "${name}" "${description}" "${topics}"
done

echo "Done."
