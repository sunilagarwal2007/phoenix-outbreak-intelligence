#!/bin/bash

# Phoenix Outbreak Intelligence - Quick Deploy to Cloud Run
# This script deploys the Flask web app with MCP integration to GCP

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"qwiklabs-gcp-03-e96cc2da1c33"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="phoenix-webapp"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "🚀 Starting Phoenix Outbreak Intelligence deployment..."
echo "📝 Project ID: $PROJECT_ID"
echo "🌍 Region: $REGION"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install: https://cloud.google.com/sdk/install"
    exit 1
fi

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not logged in to gcloud. Please run: gcloud auth login"
    exit 1
fi

# Set project
echo "📝 Setting project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable bigquery.googleapis.com

echo ""
echo "🏗️ Building container image..."
echo "Image: $IMAGE_NAME"
gcloud builds submit --tag $IMAGE_NAME

echo ""
echo "☁️ Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --concurrency 80 \
  --max-instances 10 \
  --set-env-vars "PROJECT_ID=$PROJECT_ID"

echo ""
echo "✅ Deployment complete!"
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format="value(status.url)")

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         🎉 Phoenix Outbreak Intelligence - DEPLOYED!         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Your app is live at:"
echo "   $SERVICE_URL"
echo ""
echo "🧪 Test your deployment:"
echo ""
echo "1. Health Check:"
echo "   curl $SERVICE_URL/health"
echo ""
echo "2. Test Rumor Validation (MCP Web Reader):"
echo "   curl -X POST $SERVICE_URL/api/ask \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"question\":\"I heard a new variant in Mumbai has 60% fatality. Is it true?\"}'"
echo ""
echo "3. Test Health Symptoms (MCP Maps):"
echo "   curl -X POST $SERVICE_URL/api/ask \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"question\":\"I have fever and cough in San Francisco. Where should I go?\"}'"
echo ""
echo "4. Open in browser:"
echo "   open $SERVICE_URL"
echo ""
echo "📊 Monitoring:"
echo "   Cloud Console: https://console.cloud.google.com/run?project=$PROJECT_ID"
echo "   Logs: gcloud logs read --project=$PROJECT_ID --limit=20"
echo ""
echo "🎯 Hackathon Features:"
echo "   ✅ BigQuery Integration - 8 SQL queries for outbreak data"
echo "   ✅ ADK Multi-Agent System - 4 agents with orchestration"
echo "   ✅ MCP Integration - Web Reader + Google Maps tools"
echo "   ✅ Gemini AI - Real-time insights generation"
echo "   ✅ Security - IAM roles and service accounts"
echo "   ✅ Beautiful UI - Responsive chat interface"
echo ""
echo "🎉 Your Phoenix Outbreak Intelligence system is ready!"
