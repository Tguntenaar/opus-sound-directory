#!/usr/bin/env bash
# Push main to https://github.com/Tguntenaar/opus-sound-directory (keeps origin remote intact).
set -euo pipefail
cd "$(dirname "$0")/.."

if ! gh auth status -h github.com &>/dev/null; then
  if [[ -z "${GH_TOKEN:-}" && -z "${GITHUB_TOKEN:-}" ]]; then
    echo "Not logged into GitHub. Set GH_TOKEN (repo scope) or run: gh auth login"
    exit 1
  fi
fi

REPO="Tguntenaar/opus-sound-directory"

if gh repo view "$REPO" &>/dev/null; then
  gh repo edit "$REPO" --visibility public --accept-visibility-change-consequences 2>/dev/null || \
    gh repo edit "$REPO" --visibility public
else
  gh repo create "$REPO" --public --description "Opus Sounds Directory — synthesised audio catalog (vinext / Cloudflare Workers)"
fi

if git remote get-url github &>/dev/null; then
  git remote set-url github "https://github.com/${REPO}.git"
else
  git remote add github "https://github.com/${REPO}.git"
fi

git push -u github main
echo "Pushed to https://github.com/${REPO}"
