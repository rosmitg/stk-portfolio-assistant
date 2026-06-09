#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="stk-portfolio-assistant-498901"

SECRETS=(
  ANTHROPIC_API_KEY
  VOYAGE_API_KEY
  NEWS_API_KEY
  LANGCHAIN_API_KEY
  LANGCHAIN_PROJECT
  DATABASE_URL
)

# ── helpers ────────────────────────────────────────────────────────────────────

secret_exists() {
  gcloud secrets describe "$1" --project="$PROJECT_ID" &>/dev/null
}

create_secret() {
  local name="$1"
  local value="$2"
  gcloud secrets create "$name" \
    --project="$PROJECT_ID" \
    --replication-policy="automatic"
  printf '%s' "$value" | \
    gcloud secrets versions add "$name" \
      --project="$PROJECT_ID" \
      --data-file=-
  echo "  created  $name"
}

# ── main ───────────────────────────────────────────────────────────────────────

echo "Project: $PROJECT_ID"
echo "Setting up ${#SECRETS[@]} secrets in GCP Secret Manager..."
echo

for SECRET in "${SECRETS[@]}"; do
  if secret_exists "$SECRET"; then
    echo "  exists   $SECRET (skipped)"
  else
    # Prompt for the value so nothing is hardcoded or logged
    read -r -s -p "  Enter value for $SECRET: " VALUE
    echo
    if [[ -z "$VALUE" ]]; then
      echo "  skipped  $SECRET (empty value)"
      continue
    fi
    create_secret "$SECRET" "$VALUE"
  fi
done

echo
echo "Done. Verify with:"
echo "  gcloud secrets list --project=$PROJECT_ID"
