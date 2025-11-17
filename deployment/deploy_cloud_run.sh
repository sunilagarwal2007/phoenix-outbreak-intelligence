#!/bin/bash

# Phoenix Outbreak Intelligence - Cloud Run Deployment Script
# Deploys the complete Phoenix multi-agent system to Google Cloud Run

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"phoenix-outbreak-intelligence"}
REGION=${REGION:-"us-central1"}
BASE_SERVICE_NAME="phoenix"

echo "Starting Phoenix Outbreak Intelligence Cloud Run deployment..."

# Check if user is logged in to gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Not logged in to gcloud. Please run: gcloud auth login"
    exit 1
fi

# Set project
echo "Setting project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable maps-backend.googleapis.com
gcloud services enable aiplatform.googleapis.com

# Create shared service account
SERVICE_ACCOUNT_EMAIL="phoenix-system@${PROJECT_ID}.iam.gserviceaccount.com"
echo "Creating shared service account..."
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL >/dev/null 2>&1; then
    gcloud iam service-accounts create phoenix-system \
        --display-name="Phoenix Outbreak Intelligence System" \
        --description="Shared service account for Phoenix multi-agent system"
fi

# Grant comprehensive permissions
echo "Granting permissions..."
ROLES=(
    "roles/bigquery.dataViewer"
    "roles/bigquery.jobUser"
    "roles/secretmanager.secretAccessor"
    "roles/aiplatform.user"
    "roles/run.invoker"
    "roles/logging.logWriter"
    "roles/monitoring.metricWriter"
)

for role in "${ROLES[@]}"; do
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$role"
done

# Create secrets for API keys
echo "Creating secrets..."
echo -n "your-google-maps-api-key" | gcloud secrets create google-maps-api-key \
    --data-file=- --replication-policy="automatic" || true

echo -n "your-openai-api-key" | gcloud secrets create openai-api-key \
    --data-file=- --replication-policy="automatic" || true

echo -n "your-vertex-ai-api-key" | gcloud secrets create vertex-ai-api-key \
    --data-file=- --replication-policy="automatic" || true

# Grant access to secrets
for secret in google-maps-api-key openai-api-key vertex-ai-api-key; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/secretmanager.secretAccessor" || true
done

# Deploy each agent as a separate Cloud Run service
cd "$(dirname "$0")/../"

deploy_agent() {
    local agent_name=$1
    local agent_path=$2
    local service_name="${BASE_SERVICE_NAME}-${agent_name}"
    
    echo "🏗️ Building $agent_name agent..."
    
    # Create Dockerfile for the agent
    cat > "${agent_path}/Dockerfile" << EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    curl \\
    wkhtmltopdf \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
COPY ../../mcp/ ./mcp/ 2>/dev/null || true

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8080/health || exit 1

# Run the agent
CMD ["python", "agent.py"]
EOF

    # Build and push image
    IMAGE_URI="gcr.io/$PROJECT_ID/$service_name:latest"
    gcloud builds submit --tag $IMAGE_URI "${agent_path}/"
    
    # Deploy to Cloud Run
    echo "Deploying $service_name to Cloud Run..."
    gcloud run deploy $service_name \
        --image=$IMAGE_URI \
        --platform=managed \
        --region=$REGION \
        --service-account=$SERVICE_ACCOUNT_EMAIL \
        --set-env-vars="PROJECT_ID=$PROJECT_ID,REGION=$REGION" \
        --set-secrets="GOOGLE_MAPS_API_KEY=google-maps-api-key:latest,OPENAI_API_KEY=openai-api-key:latest,VERTEX_AI_API_KEY=vertex-ai-api-key:latest" \
        --memory=2Gi \
        --cpu=1 \
        --concurrency=80 \
        --timeout=300 \
        --max-instances=10 \
        --allow-unauthenticated \
        --quiet
    
    # Get service URL
    local service_url=$(gcloud run services describe $service_name \
        --region=$REGION \
        --format="value(status.url)")
    
    echo "✅ $agent_name deployed: $service_url"
    
    # Store URL in environment variable for orchestrator
    export "${agent_name^^}_SERVICE_URL=$service_url"
    
    # Cleanup
    rm -f "${agent_path}/Dockerfile"
}

# Deploy individual agents
echo "🤖 Deploying individual agents..."
deploy_agent "data-intel" "agents/data_intel_agent"
deploy_agent "public-guidance" "agents/public_guidance_agent"
deploy_agent "resource-report" "agents/resource_report_agent_A2A"

# Deploy orchestrator with service URLs
echo "🎯 Deploying orchestrator..."
cd agents/orchestrator

# Create environment file for orchestrator
cat > .env << EOF
PROJECT_ID=$PROJECT_ID
REGION=$REGION
DATA_INTEL_SERVICE_URL=$DATA_INTEL_SERVICE_URL
PUBLIC_GUIDANCE_SERVICE_URL=$PUBLIC_GUIDANCE_SERVICE_URL
RESOURCE_REPORT_SERVICE_URL=$RESOURCE_REPORT_SERVICE_URL
EOF

# Deploy orchestrator
SERVICE_NAME="${BASE_SERVICE_NAME}-orchestrator"
IMAGE_URI="gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"

cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY ../../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
COPY ../../mcp/ ./mcp/

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run the orchestrator
CMD ["python", "workflow.py"]
EOF

gcloud builds submit --tag $IMAGE_URI .

gcloud run deploy $SERVICE_NAME \
    --image=$IMAGE_URI \
    --platform=managed \
    --region=$REGION \
    --service-account=$SERVICE_ACCOUNT_EMAIL \
    --env-vars-file=.env \
    --set-secrets="GOOGLE_MAPS_API_KEY=google-maps-api-key:latest,OPENAI_API_KEY=openai-api-key:latest,VERTEX_AI_API_KEY=vertex-ai-api-key:latest" \
    --memory=4Gi \
    --cpu=2 \
    --concurrency=80 \
    --timeout=600 \
    --max-instances=5 \
    --allow-unauthenticated \
    --quiet

ORCHESTRATOR_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --format="value(status.url)")

# Deploy MCP tools as separate services
echo "🛠️ Deploying MCP tools..."
deploy_agent "maps-mcp" "mcp/google_maps"
deploy_agent "web-reader-mcp" "mcp/web_reader"

# Create API Gateway for unified access
echo "Setting up API Gateway..."
cat > api_config.yaml << EOF
swagger: '2.0'
info:
  title: Phoenix Outbreak Intelligence API
  description: Unified API for Phoenix multi-agent system
  version: 1.0.0
schemes:
  - https
produces:
  - application/json
paths:
  /analyze:
    post:
      summary: Full outbreak analysis
      operationId: analyzeOutbreak
      x-google-backend:
        address: $ORCHESTRATOR_URL
      parameters:
        - name: body
          in: body
          required: true
          schema:
            type: object
      responses:
        200:
          description: Analysis complete
  /risk-score:
    post:
      summary: Calculate risk score
      operationId: calculateRisk
      x-google-backend:
        address: $DATA_INTEL_SERVICE_URL
      responses:
        200:
          description: Risk score calculated
  /guidance:
    post:
      summary: Generate public guidance
      operationId: generateGuidance
      x-google-backend:
        address: $PUBLIC_GUIDANCE_SERVICE_URL
      responses:
        200:
          description: Guidance generated
  /resources:
    post:
      summary: Generate resource report
      operationId: generateResources
      x-google-backend:
        address: $RESOURCE_REPORT_SERVICE_URL
      responses:
        200:
          description: Resource report generated
EOF

# Deploy API Gateway
gcloud api-gateway api-configs create phoenix-config \
    --api=phoenix-api \
    --openapi-spec=api_config.yaml \
    --project=$PROJECT_ID || true

gcloud api-gateway gateways create phoenix-gateway \
    --api=phoenix-api \
    --api-config=phoenix-config \
    --location=$REGION \
    --project=$PROJECT_ID || true

GATEWAY_URL=$(gcloud api-gateway gateways describe phoenix-gateway \
    --location=$REGION \
    --format="value(defaultHostname)")

echo "Phoenix Outbreak Intelligence deployment completed!"
echo ""
echo "Deployment Summary:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service Account: $SERVICE_ACCOUNT_EMAIL"
echo ""
echo "Service URLs:"
echo "  Main Orchestrator: $ORCHESTRATOR_URL"
echo "  Data Intelligence: $DATA_INTEL_SERVICE_URL"
echo "  Public Guidance: $PUBLIC_GUIDANCE_SERVICE_URL"
echo "  Resource Report: $RESOURCE_REPORT_SERVICE_URL"
echo "  API Gateway: https://$GATEWAY_URL"
echo ""
echo "Testing endpoints:"
echo "  Health Check: curl $ORCHESTRATOR_URL/health"
echo "  Full Analysis: curl -X POST $ORCHESTRATOR_URL/analyze -d '{\"location\":\"California\"}' -H 'Content-Type: application/json'"
echo ""
echo "Monitoring:"
echo "  Cloud Run Console: https://console.cloud.google.com/run?project=$PROJECT_ID"
echo "  Logs: gcloud logs read --project=$PROJECT_ID --limit=50"
echo ""
echo "Phoenix Outbreak Intelligence is live and ready for action!"

# Cleanup temporary files
rm -f api_config.yaml .env Dockerfile