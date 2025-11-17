#!/bin/bash

# Phoenix Outbreak Intelligence - A2A Resource Report Agent Deployment
# Deploys the Resource Report Agent as an autonomous A2A agent on Cloud Run

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"phoenix-outbreak-intelligence"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="phoenix-resource-agent-a2a"
SERVICE_ACCOUNT_EMAIL="phoenix-resource-agent@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Starting A2A Resource Report Agent deployment..."

# Check if user is logged in to gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Not logged in to gcloud. Please run: gcloud auth login"
    exit 1
fi

# Set project
echo "📝 Setting project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable maps-backend.googleapis.com

# Create service account if it doesn't exist
echo "👤 Creating service account for A2A agent..."
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL >/dev/null 2>&1; then
    gcloud iam service-accounts create phoenix-resource-agent \
        --display-name="Phoenix A2A Resource Agent" \
        --description="Autonomous A2A agent for resource planning and capacity analysis"
fi

# Grant necessary permissions
echo "Granting A2A agent permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudsql.client"

# Create secrets for API keys
echo "Creating secrets..."
echo -n "your-google-maps-api-key" | gcloud secrets create google-maps-api-key \
    --data-file=- --replication-policy="automatic" || true

echo -n "your-bigquery-service-account-key" | gcloud secrets create bigquery-sa-key \
    --data-file=- --replication-policy="automatic" || true

# Grant access to secrets
gcloud secrets add-iam-policy-binding google-maps-api-key \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding bigquery-sa-key \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor"

# Build and deploy the A2A agent
echo "🏗️ Building A2A Resource Agent container..."
cd "$(dirname "$0")/../agents/resource_report_agent_A2A"

# Create Dockerfile for A2A agent
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PDF generation and geographic analysis
RUN apt-get update && apt-get install -y \
    gcc \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY . .
COPY ../../mcp/ ./mcp/

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run the A2A agent
CMD ["python", "agent.py"]
EOF

# Create Cloud Run service configuration
cat > service.yaml << EOF
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: $SERVICE_NAME
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/execution-environment: gen2
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/execution-environment: gen2
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      serviceAccountName: $SERVICE_ACCOUNT_EMAIL
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
      - image: gcr.io/$PROJECT_ID/$SERVICE_NAME:latest
        ports:
        - name: http1
          containerPort: 8080
        env:
        - name: PROJECT_ID
          value: $PROJECT_ID
        - name: REGION
          value: $REGION
        - name: SERVICE_NAME
          value: $SERVICE_NAME
        - name: GOOGLE_MAPS_API_KEY
          valueFrom:
            secretKeyRef:
              name: google-maps-api-key
              key: latest
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
          requests:
            cpu: "1"
            memory: "2Gi"
EOF

echo "Building and pushing Docker image..."
IMAGE_URI="gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"
gcloud builds submit --tag $IMAGE_URI .

echo "Deploying to Cloud Run..."
gcloud run services replace service.yaml --region=$REGION

# Wait for deployment to complete
echo "Waiting for deployment to complete..."
gcloud run services wait $SERVICE_NAME --region=$REGION

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --format="value(status.url)")

# Configure A2A agent settings
echo "Configuring A2A agent settings..."
cat > a2a_config.json << EOF
{
  "agent_id": "phoenix-resource-agent-a2a",
  "agent_type": "AUTONOMOUS_A2A",
  "capabilities": [
    "RESOURCE_PLANNING",
    "CAPACITY_ANALYSIS", 
    "GEOGRAPHIC_OPTIMIZATION",
    "COST_ESTIMATION",
    "PROCUREMENT_RECOMMENDATIONS"
  ],
  "autonomy_level": "HIGH",
  "decision_authority": {
    "resource_recommendations": true,
    "capacity_planning": true,
    "cost_analysis": true,
    "geographic_routing": true
  },
  "integration_endpoints": {
    "webhook_url": "$SERVICE_URL/webhook",
    "health_check": "$SERVICE_URL/health",
    "metrics": "$SERVICE_URL/metrics"
  },
  "scheduling": {
    "periodic_analysis": "0 */6 * * *",
    "alert_monitoring": "continuous",
    "report_generation": "0 8 * * *"
  }
}
EOF

# Create Cloud Scheduler job for periodic execution
echo "Setting up periodic execution..."
gcloud scheduler jobs create http phoenix-resource-agent-periodic \
    --schedule="0 */6 * * *" \
    --uri="$SERVICE_URL/analyze" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --message-body='{"trigger":"periodic","scope":"all_regions"}' \
    --location=$REGION || true

echo "A2A Resource Report Agent deployment completed!"

# Test the deployed agent
echo "Testing A2A agent..."
curl -X POST "$SERVICE_URL/health" \
    -H "Content-Type: application/json" \
    -w "\nStatus: %{http_code}\n"

echo "Deployment Summary:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service Name: $SERVICE_NAME"
echo "  Service URL: $SERVICE_URL"
echo "  Service Account: $SERVICE_ACCOUNT_EMAIL"
echo ""
echo "Access points:"
echo "  Health Check: $SERVICE_URL/health"
echo "  Analyze Endpoint: $SERVICE_URL/analyze"
echo "  Metrics: $SERVICE_URL/metrics"
echo ""
echo "Monitoring:"
echo "  Logs: gcloud logs read 'resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME' --project=$PROJECT_ID"
echo "  Metrics: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"
echo ""
echo "To trigger manual analysis:"
echo "  curl -X POST '$SERVICE_URL/analyze' -H 'Content-Type: application/json' -d '{\"location\":\"California\"}'"

# Cleanup temporary files
rm -f Dockerfile service.yaml a2a_config.json

echo "Phoenix A2A Resource Agent is live and autonomous!"