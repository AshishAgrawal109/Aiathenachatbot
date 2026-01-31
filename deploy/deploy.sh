#!/bin/bash
# Deploy AIATHENA Agent to Google Cloud Platform with Secret Manager
# 
# This script:
# 1. Creates secrets in GCP Secret Manager
# 2. Builds and pushes Docker image
# 3. Deploys to Cloud Run with Secret Manager integration
#
# Usage:
#   ./deploy/deploy.sh [PROJECT_ID] [REGION]
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - Docker installed
#   - A GCP project with billing enabled

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${2:-us-central1}"
SERVICE_NAME="aiathena-agent"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${GREEN}🦉 Deploying AIATHENA Agent to GCP${NC}"
echo "   Project: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo ""

# Check if gcloud is authenticated
if ! gcloud auth print-identity-token &> /dev/null; then
    echo -e "${RED}❌ Not authenticated with gcloud. Run: gcloud auth login${NC}"
    exit 1
fi

# Set project
gcloud config set project "${PROJECT_ID}"

# Enable required APIs
echo -e "\n${YELLOW}📦 Enabling required APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com \
    containerregistry.googleapis.com \
    --project="${PROJECT_ID}"

# ============================================
# SECRET MANAGER SETUP
# ============================================
echo -e "\n${YELLOW}🔐 Setting up Secret Manager...${NC}"

# Function to create or update a secret
create_or_update_secret() {
    local secret_name=$1
    local prompt_text=$2
    
    # Check if secret exists
    if gcloud secrets describe "${secret_name}" --project="${PROJECT_ID}" &> /dev/null; then
        echo -e "   Secret ${GREEN}${secret_name}${NC} exists."
        read -p "   Update it? (y/N): " update_choice
        if [[ "${update_choice}" != "y" && "${update_choice}" != "Y" ]]; then
            return
        fi
    fi
    
    # Prompt for value
    echo -e "   ${prompt_text}"
    read -s -p "   Enter value (hidden): " secret_value
    echo ""
    
    if [[ -z "${secret_value}" ]]; then
        echo -e "   ${YELLOW}⚠️  Skipping ${secret_name} (empty value)${NC}"
        return
    fi
    
    # Create or update secret
    if gcloud secrets describe "${secret_name}" --project="${PROJECT_ID}" &> /dev/null; then
        echo -n "${secret_value}" | gcloud secrets versions add "${secret_name}" \
            --data-file=- \
            --project="${PROJECT_ID}"
        echo -e "   ${GREEN}✓${NC} Updated ${secret_name}"
    else
        echo -n "${secret_value}" | gcloud secrets create "${secret_name}" \
            --data-file=- \
            --replication-policy="automatic" \
            --project="${PROJECT_ID}"
        echo -e "   ${GREEN}✓${NC} Created ${secret_name}"
    fi
}

# Create secrets
echo ""
create_or_update_secret "aiathena-moltbook-token" "Moltbook Agent Token (get from moltbook.com after registration)"
echo ""
create_or_update_secret "aiathena-gemini-key" "Gemini API Key (get from aistudio.google.com/apikey)"

# Get the Cloud Run service account
echo -e "\n${YELLOW}🔑 Setting up IAM permissions...${NC}"
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Grant Secret Manager access to Cloud Run service account
for secret_name in "aiathena-moltbook-token" "aiathena-gemini-key"; do
    if gcloud secrets describe "${secret_name}" --project="${PROJECT_ID}" &> /dev/null; then
        gcloud secrets add-iam-policy-binding "${secret_name}" \
            --member="serviceAccount:${SERVICE_ACCOUNT}" \
            --role="roles/secretmanager.secretAccessor" \
            --project="${PROJECT_ID}" \
            --quiet 2>/dev/null || true
        echo -e "   ${GREEN}✓${NC} Granted access to ${secret_name}"
    fi
done

# ============================================
# BUILD AND DEPLOY
# ============================================

# Build the Docker image
echo -e "\n${YELLOW}🔨 Building Docker image...${NC}"
docker build -t "${IMAGE_NAME}:latest" .

# Push to Container Registry
echo -e "\n${YELLOW}📤 Pushing to Container Registry...${NC}"
docker push "${IMAGE_NAME}:latest"

# Deploy to Cloud Run
echo -e "\n${YELLOW}☁️  Deploying to Cloud Run...${NC}"
gcloud run deploy "${SERVICE_NAME}" \
    --image="${IMAGE_NAME}:latest" \
    --region="${REGION}" \
    --platform=managed \
    --no-allow-unauthenticated \
    --min-instances=1 \
    --max-instances=1 \
    --memory=512Mi \
    --timeout=3600 \
    --set-env-vars="MOLTBOOK_API_URL=https://www.moltbook.com/api/v1,MOLTBOOK_AGENT_NAME=AIATHENA,GEMINI_MODEL=gemini-2.5-pro,GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --set-secrets="MOLTBOOK_AGENT_TOKEN=aiathena-moltbook-token:latest,GOOGLE_API_KEY=aiathena-gemini-key:latest" \
    --project="${PROJECT_ID}"

# Get service URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --format="value(status.url)")

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Service Details:${NC}"
echo "   Name: ${SERVICE_NAME}"
echo "   URL: ${SERVICE_URL}"
echo "   Region: ${REGION}"
echo ""
echo -e "${YELLOW}🔐 Secrets in Secret Manager:${NC}"
echo "   - aiathena-moltbook-token"
echo "   - aiathena-gemini-key"
echo ""
echo -e "${YELLOW}📝 Useful Commands:${NC}"
echo ""
echo "   View logs:"
echo "   gcloud run logs read ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID}"
echo ""
echo "   Update a secret:"
echo "   echo 'new-value' | gcloud secrets versions add aiathena-gemini-key --data-file=-"
echo ""
echo "   Restart service (to pick up new secrets):"
echo "   gcloud run services update ${SERVICE_NAME} --region=${REGION}"
