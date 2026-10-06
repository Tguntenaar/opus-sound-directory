#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
NODE="${PLAYWRIGHT_NODE:-node}"
export NEXT_PUBLIC_POSTHOG_KEY="${NEXT_PUBLIC_POSTHOG_KEY:-phc_playwright_test_key}"
"$NODE" node_modules/vite/bin/vite.js build
exec npx wrangler dev \
  --config wrangler.temporary.jsonc \
  --port "${PLAYWRIGHT_PORT:-43125}" \
  --local-protocol http \
  --ip 127.0.0.1
