#!/usr/bin/env bash
# Signal Loom AI — Cloudflare Pages Deploy Script
# Usage: ./deploy.sh
#
# Requires:
#   CLOUDFLARE_API_TOKEN — Cloudflare API token (cfat_xxx)
#   CF_ACCOUNT_ID — Cloudflare Account ID
#   CF_PROJECT_NAME — Pages project name
#
# Get these from: https://dash.cloudflare.com

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LANDING_DIR="${SCRIPT_DIR}"

# Config — update these
CF_ACCOUNT_ID="${CF_ACCOUNT_ID:-17d8cd82c85219f0b6e0099568840c80}"
CF_PROJECT_NAME="${CF_PROJECT_NAME:-signalloom-landing}"
CLOUDFLARE_API_TOKEN="${CLOUDFLARE_API_TOKEN:-}"

if [[ -z "$CLOUDFLARE_API_TOKEN" ]]; then
  echo "❌ Missing CLOUDFLARE_API_TOKEN"
  echo "   Set it: export CLOUDFLARE_API_TOKEN='cfat_xxx'"
  echo "   Get one at: My Profile → API Tokens → Create Custom Token"
  echo "   Permission needed: Account → Cloudflare Pages → Edit"
  exit 1
fi

echo "📦 Deploying ${CF_PROJECT_NAME} to Cloudflare Pages..."
echo "   Account: ${CF_ACCOUNT_ID}"

# Deploy using wrangler
cd "$LANDING_DIR"
CLOUDFLARE_API_TOKEN="$CLOUDFLARE_API_TOKEN" \
  npx wrangler pages deploy . \
  --project-name="$CF_PROJECT_NAME" \
  --branch=main \
  --commit-dirty=true

echo ""
echo "✅ Deploy complete!"
echo "   Preview: https://${CF_PROJECT_NAME}.pages.dev"
echo ""
echo "   To set a custom domain (signalloomai.com):"
echo "   1. Add signalloomai.com to Cloudflare (dash.cloudflare.com)"
echo "   2. Add CNAME at GoDaddy: www → ${CF_PROJECT_NAME}.pages.dev"
echo "   3. Or transfer domain to Cloudflare for full control"
