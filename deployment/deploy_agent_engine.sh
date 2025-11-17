#!/bin/bash

# Phoenix Outbreak Intelligence - Agent Engine Deployment Script
# Deploys the multi-agent orchestrator to Google Cloud Vertex AI Agent Engine

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"phoenix-outbreak-intelligence"}
REGION=${REGION:-"us-central1"}
AGENT_NAME="phoenix-orchestrator"
SERVICE_ACCOUNT_EMAIL="phoenix-agents@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Starting Phoenix Agent Engine deployment..."

# Check if user is logged in to gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Not logged in to gcloud. Please run: gcloud auth login"
    exit 1
fi

# Set project
echo "Setting project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Create service account if it doesn't exist
echo "Creating service account..."
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL >/dev/null 2>&1; then
    gcloud iam service-accounts create phoenix-agents \
        --display-name="Phoenix Outbreak Intelligence Agents" \
        --description="Service account for Phoenix multi-agent system"
fi

# Grant necessary permissions
echo "Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor"

# Build and push container image
echo "🏗️ Building container image..."
cd "$(dirname "$0")/../"

cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agents/ ./agents/
COPY mcp/ ./mcp/

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the orchestrator
CMD ["python", "-m", "agents.orchestrator.workflow"]
EOF

# Build and push to Container Registry
echo "Building Docker image..."
IMAGE_URI="gcr.io/$PROJECT_ID/$AGENT_NAME:latest"
gcloud builds submit --tag $IMAGE_URI .

# Deploy to Vertex AI Agent Engine
echo "Deploying to Vertex AI Agent Engine..."

# Create agent configuration
cat > agent_config.json << EOF
{
  "displayName": "Phoenix Outbreak Intelligence Orchestrator",
  "description": "Multi-agent system for outbreak intelligence and response coordination",
  "agentHumanConfig": {
    "allowHumanInTheLoop": true,
    "humanEscalationConfig": {
      "escalationMessage": "This conversation requires human oversight due to critical outbreak conditions."
    }
  },
  "agentToolConfig": {
    "openApiTools": [
      {
        "displayName": "Data Intelligence Agent",
        "description": "Analyzes outbreak data and calculates risk scores"
      },
      {
        "displayName": "Public Guidance Agent", 
        "description": "Generates public health guidance and recommendations"
      },
      {
        "displayName": "Resource Report Agent",
        "description": "Analyzes healthcare resource needs and capacity planning"
      }
    ]
  },
  "conversationConfig": {
    "maxTurns": 50,
    "responseTimeout": "30s"
  }
}
EOF

# Create the agent
gcloud alpha aiplatform agents create \
    --region=$REGION \
    --display-name="$AGENT_NAME" \
    --config-from-file=agent_config.json \
    --service-account=$SERVICE_ACCOUNT_EMAIL

echo "Agent Engine deployment completed!"

# Get agent details
AGENT_ID=$(gcloud alpha aiplatform agents list \
    --region=$REGION \
    --filter="displayName:$AGENT_NAME" \
    --format="value(name)" | head -1)

echo "Deployment Summary:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Agent ID: $AGENT_ID"
echo "  Service Account: $SERVICE_ACCOUNT_EMAIL"
echo ""
echo "Access your agent at:"
echo "  https://console.cloud.google.com/aiplatform/agents?project=$PROJECT_ID"
echo ""
echo "🔧 To test the agent:"
echo "  gcloud alpha aiplatform agents chat --region=$REGION --agent=$AGENT_ID"

# Cleanup temporary files
rm -f Dockerfile agent_config.json

echo "Phoenix Outbreak Intelligence Agent Engine is ready!"