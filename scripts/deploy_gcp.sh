#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${ENV_FILE:-.env.gcp_deployment}"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

if ! command -v gcloud >/dev/null; then
  echo "gcloud not found. Install Google Cloud SDK first."
  exit 1
fi

if ! command -v docker >/dev/null; then
  echo "docker not found. Install Docker first."
  exit 1
fi

PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-us-central1}"
REPO_NAME="${REPO_NAME:-bgpy-repo}"
BACKEND_SERVICE="${BACKEND_SERVICE:-bgpy-backend}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-bgpy-frontend}"
CUSTOM_DOMAINS="${CUSTOM_DOMAINS:-}"

DB_INSTANCE="${DB_INSTANCE:-bgpy-sql}"
DB_NAME="${DB_NAME:-bgpy}"
DB_USER="${DB_USER:-bgpy}"
DB_PASSWORD="${DB_PASSWORD:-}"

OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"

ACTION="${1:-deploy}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "PROJECT_ID is required."
  exit 1
fi

if [[ -z "$DB_PASSWORD" ]]; then
  echo "DB_PASSWORD is required."
  exit 1
fi

gcloud config set project "$PROJECT_ID"

if [[ "$ACTION" != "fix-env" ]]; then
  echo "Enabling required services..."
  gcloud services enable run.googleapis.com artifactregistry.googleapis.com sqladmin.googleapis.com
fi

if [[ "$ACTION" != "fix-env" ]]; then
  echo "Ensuring Artifact Registry exists..."
  if ! gcloud artifacts repositories describe "$REPO_NAME" --location "$REGION" >/dev/null 2>&1; then
    gcloud artifacts repositories create "$REPO_NAME" --repository-format=docker --location "$REGION"
  fi
fi

if [[ "$ACTION" != "fix-env" ]]; then
  echo "Ensuring Cloud SQL instance exists..."
  if ! gcloud sql instances describe "$DB_INSTANCE" >/dev/null 2>&1; then
    gcloud sql instances create "$DB_INSTANCE" \
      --database-version=POSTGRES_15 \
      --cpu=1 --memory=4GB \
      --region="$REGION"
  fi
fi

if [[ "$ACTION" != "fix-env" ]]; then
  echo "Ensuring database exists..."
  if ! gcloud sql databases describe "$DB_NAME" --instance="$DB_INSTANCE" >/dev/null 2>&1; then
    gcloud sql databases create "$DB_NAME" --instance="$DB_INSTANCE"
  fi
fi

if [[ "$ACTION" != "fix-env" ]]; then
  echo "Ensuring database user exists..."
  if ! gcloud sql users list --instance="$DB_INSTANCE" --format="value(name)" | grep -q "^${DB_USER}$"; then
    gcloud sql users create "$DB_USER" --instance="$DB_INSTANCE" --password="$DB_PASSWORD"
  fi
fi

PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")"
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/cloudsql.client" >/dev/null

CONNECTION_NAME="$(gcloud sql instances describe "$DB_INSTANCE" --format="value(connectionName)")"
DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CONNECTION_NAME}"

if [[ "$ACTION" != "fix-env" ]]; then
  echo "Configuring docker auth for Artifact Registry..."
  gcloud auth configure-docker "${REGION}-docker.pkg.dev" -q
fi

BACKEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/bgpy-backend"
FRONTEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/bgpy-frontend"

if [[ "$ACTION" != "fix-env" && "$ACTION" != "frontend-only" ]]; then
  echo "Building backend image..."
  docker build -f webapp/backend/Dockerfile -t "${BACKEND_IMAGE}" .
  docker push "${BACKEND_IMAGE}"
fi

if [[ "$ACTION" != "fix-env" && "$ACTION" != "frontend-only" ]]; then
  echo "Deploying backend to Cloud Run..."
  gcloud run deploy "$BACKEND_SERVICE" \
    --image "${BACKEND_IMAGE}" \
    --platform managed --region "$REGION" \
    --allow-unauthenticated \
    --add-cloudsql-instances "$CONNECTION_NAME" \
    --set-env-vars "DATABASE_URL=${DATABASE_URL},OPENROUTER_API_KEY=${OPENROUTER_API_KEY}"
fi

BACKEND_URL="$(gcloud run services describe "$BACKEND_SERVICE" --region "$REGION" --format="value(status.url)")"

if [[ "$ACTION" != "fix-env" && "$ACTION" != "backend-only" ]]; then
  echo "Building frontend image..."
  docker build -f webapp/frontend/Dockerfile -t "${FRONTEND_IMAGE}" .
  docker push "${FRONTEND_IMAGE}"
fi

if [[ "$ACTION" != "fix-env" && "$ACTION" != "backend-only" ]]; then
  echo "Deploying frontend to Cloud Run..."
  gcloud run deploy "$FRONTEND_SERVICE" \
    --image "${FRONTEND_IMAGE}" \
    --platform managed --region "$REGION" \
    --allow-unauthenticated \
    --set-env-vars "VITE_API_URL=${BACKEND_URL}"
fi

FRONTEND_URL="$(gcloud run services describe "$FRONTEND_SERVICE" --region "$REGION" --format="value(status.url)")"

echo "Updating backend env vars (DB, OpenRouter)..."
gcloud run services update "$BACKEND_SERVICE" \
  --region "$REGION" \
  --update-env-vars "DATABASE_URL=${DATABASE_URL},OPENROUTER_API_KEY=${OPENROUTER_API_KEY}"

echo "Updating frontend env vars (API URL)..."
gcloud run services update "$FRONTEND_SERVICE" \
  --region "$REGION" \
  --update-env-vars "VITE_API_URL=${BACKEND_URL}"

echo "Done."
echo "Backend:  ${BACKEND_URL}"
echo "Frontend: ${FRONTEND_URL}"
