#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="stk-portfolio-assistant-498901"
REGION="australia-southeast1"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/stk-portfolio"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

BACKEND_IMAGE="${REGISTRY}/backend"
FRONTEND_IMAGE="${REGISTRY}/frontend"

# Optional: accept a git SHA or tag as the image tag; default to 'latest'
TAG="${1:-latest}"

echo "==> Configuring Docker for Artifact Registry"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

echo "==> Building backend image"
docker build \
  --platform linux/amd64 \
  -t "${BACKEND_IMAGE}:${TAG}" \
  -t "${BACKEND_IMAGE}:latest" \
  "${REPO_ROOT}/backend"

echo "==> Building frontend image"
docker build \
  --platform linux/amd64 \
  -t "${FRONTEND_IMAGE}:${TAG}" \
  -t "${FRONTEND_IMAGE}:latest" \
  "${REPO_ROOT}/frontend"

echo "==> Pushing backend image"
docker push "${BACKEND_IMAGE}:${TAG}"
docker push "${BACKEND_IMAGE}:latest"

echo "==> Pushing frontend image"
docker push "${FRONTEND_IMAGE}:${TAG}"
docker push "${FRONTEND_IMAGE}:latest"

echo "==> Deploying backend to Cloud Run"
gcloud run deploy stk-backend \
  --image "${BACKEND_IMAGE}:${TAG}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --platform managed \
  --port 8080 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --set-secrets "ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,VOYAGE_API_KEY=VOYAGE_API_KEY:latest,NEWS_API_KEY=NEWS_API_KEY:latest,LANGCHAIN_API_KEY=LANGCHAIN_API_KEY:latest,LANGCHAIN_PROJECT=LANGCHAIN_PROJECT:latest" \
  --set-env-vars "APP_ENV=production,LANGCHAIN_TRACING_V2=true"

BACKEND_URL=$(gcloud run services describe stk-backend \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format "value(status.url)")

echo "==> Backend deployed at ${BACKEND_URL}"

echo "==> Deploying frontend to Cloud Run"
gcloud run deploy stk-frontend \
  --image "${FRONTEND_IMAGE}:${TAG}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --platform managed \
  --port 8080 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --set-env-vars "BACKEND_URL=${BACKEND_URL},APP_ENV=production"

FRONTEND_URL=$(gcloud run services describe stk-frontend \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format "value(status.url)")

echo ""
echo "==> Deployment complete"
echo "    Backend:  ${BACKEND_URL}"
echo "    Frontend: ${FRONTEND_URL}"
