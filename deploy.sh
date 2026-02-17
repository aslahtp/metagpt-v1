#!/usr/bin/env bash
#
# MetaGPT - Google Cloud Run Deployment Script
#
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh
#
# Prerequisites:
#   - gcloud CLI installed and authenticated (gcloud auth login)
#   - A GCP project with billing enabled
#   - MongoDB Atlas cluster set up with a connection string
#
# This script will:
#   1. Enable required GCP APIs
#   2. Create an Artifact Registry repository
#   3. Build and push Docker images via Cloud Build
#   4. Deploy backend and frontend to Cloud Run
#   5. Configure CORS between the two services

set -euo pipefail

# ─────────────────────────────────────────────
# Configuration - EDIT THESE BEFORE RUNNING
# ─────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID environment variable}"
REGION="${GCP_REGION:-us-central1}"
REPO_NAME="metagpt"

# Backend environment variables
MONGODB_URI="${MONGODB_URI:?Set MONGODB_URI environment variable (e.g. mongodb+srv://user:pass@cluster.mongodb.net/metagpt)}"
MONGODB_DB="${MONGODB_DB:-metagpt}"
GOOGLE_API_KEY="${GOOGLE_API_KEY:?Set GOOGLE_API_KEY environment variable}"
JWT_SECRET="${JWT_SECRET:?Set JWT_SECRET environment variable (use a long random string)}"

# Service names
BACKEND_SERVICE="metagpt-backend"
FRONTEND_SERVICE="metagpt-frontend"

# Image paths
BACKEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/backend:latest"
FRONTEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/frontend:latest"

echo "============================================"
echo "  MetaGPT - Google Cloud Run Deployment"
echo "============================================"
echo ""
echo "  Project:  ${PROJECT_ID}"
echo "  Region:   ${REGION}"
echo ""

# ─────────────────────────────────────────────
# Step 1: Set project and enable APIs
# ─────────────────────────────────────────────
echo "[1/7] Setting project and enabling APIs..."
gcloud config set project "${PROJECT_ID}" --quiet
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    --quiet

# ─────────────────────────────────────────────
# Step 2: Create Artifact Registry repository
# ─────────────────────────────────────────────
echo "[2/7] Creating Artifact Registry repository..."
gcloud artifacts repositories describe "${REPO_NAME}" \
    --location="${REGION}" \
    --format="value(name)" 2>/dev/null \
|| gcloud artifacts repositories create "${REPO_NAME}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="MetaGPT Docker images" \
    --quiet

# ─────────────────────────────────────────────
# Step 3: Build and push backend image
# ─────────────────────────────────────────────
echo "[3/7] Building backend image via Cloud Build..."
gcloud builds submit ./backend \
    --tag "${BACKEND_IMAGE}" \
    --quiet

# ─────────────────────────────────────────────
# Step 4: Deploy backend to Cloud Run
# ─────────────────────────────────────────────
echo "[4/7] Deploying backend to Cloud Run..."
gcloud run deploy "${BACKEND_SERVICE}" \
    --image "${BACKEND_IMAGE}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --port 8000 \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 3 \
    --timeout 300 \
    --set-env-vars "\
MONGODB_URI=${MONGODB_URI},\
MONGODB_DB=${MONGODB_DB},\
GOOGLE_API_KEY=${GOOGLE_API_KEY},\
JWT_SECRET=${JWT_SECRET},\
DEBUG=false,\
PROJECTS_DIR=/app/projects,\
STORAGE_TYPE=file" \
    --quiet

# Get backend URL
BACKEND_URL=$(gcloud run services describe "${BACKEND_SERVICE}" \
    --region "${REGION}" \
    --format="value(status.url)")

echo "    Backend deployed at: ${BACKEND_URL}"

# ─────────────────────────────────────────────
# Step 5: Build and push frontend image
# ─────────────────────────────────────────────
echo "[5/7] Building frontend image via Cloud Build..."
gcloud builds submit ./frontend \
    --tag "${FRONTEND_IMAGE}" \
    --quiet

# ─────────────────────────────────────────────
# Step 6: Deploy frontend to Cloud Run
# ─────────────────────────────────────────────
echo "[6/7] Deploying frontend to Cloud Run..."
gcloud run deploy "${FRONTEND_SERVICE}" \
    --image "${FRONTEND_IMAGE}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --port 3000 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 3 \
    --set-env-vars "API_URL=${BACKEND_URL}" \
    --quiet

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe "${FRONTEND_SERVICE}" \
    --region "${REGION}" \
    --format="value(status.url)")

echo "    Frontend deployed at: ${FRONTEND_URL}"

# ─────────────────────────────────────────────
# Step 7: Update backend CORS with frontend URL
# ─────────────────────────────────────────────
echo "[7/7] Updating backend CORS to allow frontend..."
gcloud run services update "${BACKEND_SERVICE}" \
    --region "${REGION}" \
    --update-env-vars "CORS_ORIGINS=[\"${FRONTEND_URL}\"]" \
    --quiet

echo ""
echo "============================================"
echo "  Deployment complete!"
echo "============================================"
echo ""
echo "  Frontend: ${FRONTEND_URL}"
echo "  Backend:  ${BACKEND_URL}"
echo "  API Docs: ${BACKEND_URL}/docs"
echo "  Health:   ${BACKEND_URL}/health"
echo ""
echo "  To redeploy after code changes, run this script again."
echo "  To tear down, delete the Cloud Run services:"
echo "    gcloud run services delete ${BACKEND_SERVICE} --region ${REGION}"
echo "    gcloud run services delete ${FRONTEND_SERVICE} --region ${REGION}"
echo ""
