#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="stk-portfolio-assistant-498901"
REGION="australia-southeast1"
INSTANCE_NAME="stk-portfolio-db"
DB_NAME="stk_portfolio"
DB_USER="stk_user"

echo "==> Creating Cloud SQL PostgreSQL 15 instance: ${INSTANCE_NAME}"
echo "    (This takes 5-10 minutes on first creation)"

if gcloud sql instances describe "${INSTANCE_NAME}" --project="${PROJECT_ID}" &>/dev/null; then
  echo "    Instance already exists — skipping creation"
else
  gcloud sql instances create "${INSTANCE_NAME}" \
    --project="${PROJECT_ID}" \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region="${REGION}" \
    --storage-type=SSD \
    --storage-size=10GB \
    --no-backup \
    --assign-ip
  echo "    Instance created"
fi

echo "==> Creating database: ${DB_NAME}"
if gcloud sql databases describe "${DB_NAME}" \
    --instance="${INSTANCE_NAME}" \
    --project="${PROJECT_ID}" &>/dev/null; then
  echo "    Database already exists — skipping"
else
  gcloud sql databases create "${DB_NAME}" \
    --instance="${INSTANCE_NAME}" \
    --project="${PROJECT_ID}"
  echo "    Database created"
fi

echo "==> Creating user: ${DB_USER}"
# Generate a cryptographically random 32-char password
PASSWORD=$(python3 -c "import secrets, string; \
  alphabet = string.ascii_letters + string.digits; \
  print(''.join(secrets.choice(alphabet) for _ in range(32)))")

if gcloud sql users describe "${DB_USER}" \
    --instance="${INSTANCE_NAME}" \
    --project="${PROJECT_ID}" &>/dev/null; then
  echo "    User already exists — updating password"
  gcloud sql users set-password "${DB_USER}" \
    --instance="${INSTANCE_NAME}" \
    --project="${PROJECT_ID}" \
    --password="${PASSWORD}"
else
  gcloud sql users create "${DB_USER}" \
    --instance="${INSTANCE_NAME}" \
    --project="${PROJECT_ID}" \
    --password="${PASSWORD}"
  echo "    User created"
fi

CONNECTION_NAME="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
DATABASE_URL="postgresql+asyncpg://${DB_USER}:${PASSWORD}@/${DB_NAME}?host=/cloudsql/${CONNECTION_NAME}"

echo ""
echo "==> DATABASE_URL:"
echo "    ${DATABASE_URL}"
echo ""

echo "==> Storing DATABASE_URL in Secret Manager"
if gcloud secrets describe "DATABASE_URL" --project="${PROJECT_ID}" &>/dev/null; then
  printf '%s' "${DATABASE_URL}" | \
    gcloud secrets versions add "DATABASE_URL" \
      --project="${PROJECT_ID}" \
      --data-file=-
  echo "    New secret version added"
else
  gcloud secrets create "DATABASE_URL" \
    --project="${PROJECT_ID}" \
    --replication-policy="automatic"
  printf '%s' "${DATABASE_URL}" | \
    gcloud secrets versions add "DATABASE_URL" \
      --project="${PROJECT_ID}" \
      --data-file=-
  echo "    Secret created and version added"
fi

echo ""
echo "==> Done"
echo "    Instance:       ${INSTANCE_NAME}"
echo "    Connection:     ${CONNECTION_NAME}"
echo "    Database:       ${DB_NAME}"
echo "    User:           ${DB_USER}"
echo "    DATABASE_URL stored in Secret Manager as DATABASE_URL"
echo ""
echo "    Add the Cloud SQL connection to your Cloud Run deploy:"
echo "    --add-cloudsql-instances=${CONNECTION_NAME}"
echo "    --set-secrets=DATABASE_URL=DATABASE_URL:latest"
