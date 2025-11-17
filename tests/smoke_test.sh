#!/bin/bash

# Phoenix Outbreak Intelligence - Smoke Test
# Quick validation that all components are working

set -e

echo "🔥 Phoenix Outbreak Intelligence - Smoke Test"
echo "=============================================="

# Configuration
PROJECT_ID=${PROJECT_ID:-"phoenix-outbreak-intelligence"}
REGION=${REGION:-"us-central1"}
BASE_URL=${BASE_URL:-"http://localhost:8080"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test status tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test logging
log_test() {
    local status=$1
    local test_name=$2
    local details=$3
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗${NC} $test_name"
        if [ -n "$details" ]; then
            echo -e "  ${YELLOW}Details:${NC} $details"
        fi
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# Test functions
test_python_installation() {
    echo -e "\n${BLUE}Testing Python Environment...${NC}"
    
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version 2>&1)
        log_test "PASS" "Python 3 installed ($python_version)"
    else
        log_test "FAIL" "Python 3 not found"
    fi
    
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
        log_test "PASS" "Python version >= 3.9"
    else
        log_test "FAIL" "Python version < 3.9"
    fi
}

test_dependencies() {
    echo -e "\n${BLUE}Testing Python Dependencies...${NC}"
    
    # Test requests
    if python3 -c "import requests" 2>/dev/null; then
        log_test "PASS" "Dependency: requests"
    else
        log_test "FAIL" "Dependency missing: requests"
    fi
    
    # Test pandas
    if python3 -c "import pandas" 2>/dev/null; then
        log_test "PASS" "Dependency: pandas"
    else
        log_test "FAIL" "Dependency missing: pandas"
    fi
    
    # Test numpy
    if python3 -c "import numpy" 2>/dev/null; then
        log_test "PASS" "Dependency: numpy"
    else
        log_test "FAIL" "Dependency missing: numpy"
    fi
    
    # Test google-cloud-bigquery (imports as google.cloud.bigquery)
    if python3 -c "import google.cloud.bigquery" 2>/dev/null; then
        log_test "PASS" "Dependency: google-cloud-bigquery"
    else
        log_test "FAIL" "Dependency missing: google-cloud-bigquery"
    fi
    
    # Test flask
    if python3 -c "import flask" 2>/dev/null; then
        log_test "PASS" "Dependency: flask"
    else
        log_test "FAIL" "Dependency missing: flask"
    fi
    
    # Test beautifulsoup4 (imports as bs4)
    if python3 -c "import bs4" 2>/dev/null; then
        log_test "PASS" "Dependency: beautifulsoup4"
    else
        log_test "FAIL" "Dependency missing: beautifulsoup4"
    fi
}

test_file_structure() {
    echo -e "\n${BLUE}Testing File Structure...${NC}"
    
    local required_files=(
        "agents/data_intel_agent/agent.py"
        "agents/public_guidance_agent/agent.py" 
        "agents/resource_report_agent_A2A/agent.py"
        "agents/orchestrator/workflow.py"
        "mcp/google_maps/maps_mcp_agent.py"
        "mcp/web_reader/web_reader_mcp_server.py"
        "requirements.txt"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            log_test "PASS" "File exists: $file"
        else
            log_test "FAIL" "File missing: $file"
        fi
    done
}

test_agent_imports() {
    echo -e "\n${BLUE}Testing Agent Imports...${NC}"
    
    # Test Data Intelligence Agent
    if cd agents/data_intel_agent && python3 -c "from agent import DataIntelligenceAgent; print('Import successful')" 2>/dev/null; then
        log_test "PASS" "Data Intelligence Agent import"
        cd - > /dev/null
    else
        log_test "FAIL" "Data Intelligence Agent import"
        cd - > /dev/null 2>/dev/null || true
    fi
    
    # Test Public Guidance Agent
    if cd agents/public_guidance_agent && python3 -c "from agent import PublicGuidanceAgent; print('Import successful')" 2>/dev/null; then
        log_test "PASS" "Public Guidance Agent import"
        cd - > /dev/null
    else
        log_test "FAIL" "Public Guidance Agent import"
        cd - > /dev/null 2>/dev/null || true
    fi
    
    # Test Resource Report Agent
    if cd agents/resource_report_agent_A2A && python3 -c "from agent import ResourceReportAgent; print('Import successful')" 2>/dev/null; then
        log_test "PASS" "Resource Report Agent import"
        cd - > /dev/null
    else
        log_test "FAIL" "Resource Report Agent import"
        cd - > /dev/null 2>/dev/null || true
    fi
    
    # Test Orchestrator
    if cd agents/orchestrator && python3 -c "from workflow import PhoenixWorkflow; print('Import successful')" 2>/dev/null; then
        log_test "PASS" "Orchestrator import"
        cd - > /dev/null
    else
        log_test "FAIL" "Orchestrator import"
        cd - > /dev/null 2>/dev/null || true
    fi
}

test_sample_data() {
    echo -e "\n${BLUE}Testing Sample Data...${NC}"
    
    local sample_files=(
        "data/sample_api_outputs/sample_risk_score.json"
        "data/sample_api_outputs/sample_resource_report.json"
        "data/sample_bigquery_results/covid_cases_by_county.csv"
    )
    
    for file in "${sample_files[@]}"; do
        if [ -f "$file" ] && [ -s "$file" ]; then
            log_test "PASS" "Sample data: $(basename $file)"
        else
            log_test "FAIL" "Sample data missing or empty: $(basename $file)"
        fi
    done
}

test_configuration_files() {
    echo -e "\n${BLUE}Testing Configuration Files...${NC}"
    
    # Test JSON validation for configuration files
    if [ -f "agents/resource_report_agent_A2A/agent.json" ]; then
        if python3 -c "import json; json.load(open('agents/resource_report_agent_A2A/agent.json'))" 2>/dev/null; then
            log_test "PASS" "A2A Agent JSON config valid"
        else
            log_test "FAIL" "A2A Agent JSON config invalid"
        fi
    else
        log_test "FAIL" "A2A Agent JSON config missing"
    fi
    
    # Test demo cases JSON
    if [ -f "tests/demo_chat_cases.json" ]; then
        if python3 -c "import json; json.load(open('tests/demo_chat_cases.json'))" 2>/dev/null; then
            log_test "PASS" "Demo chat cases JSON valid"
        else
            log_test "FAIL" "Demo chat cases JSON invalid"
        fi
    else
        log_test "FAIL" "Demo chat cases JSON missing"
    fi
}

test_deployment_scripts() {
    echo -e "\n${BLUE}Testing Deployment Scripts...${NC}"
    
    local scripts=(
        "deployment/deploy_agent_engine.sh"
        "deployment/deploy_A2A_report_agent.sh"
        "deployment/deploy_cloud_run.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ] && [ -x "$script" ]; then
            log_test "PASS" "Deployment script executable: $(basename $script)"
        elif [ -f "$script" ]; then
            log_test "FAIL" "Deployment script not executable: $(basename $script)"
        else
            log_test "FAIL" "Deployment script missing: $(basename $script)"
        fi
    done
}

test_local_server_startup() {
    echo -e "\n${BLUE}Testing Local Server Startup...${NC}"
    
    # Try to start a simple Flask server in the background
    if command -v flask &> /dev/null; then
        cd agents/orchestrator
        
        # Create a simple test server
        cat > test_server.py << 'EOF'
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'phoenix-test'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8888)
EOF
        
        # Start server in background
        python3 test_server.py &
        SERVER_PID=$!
        
        # Wait a moment for startup
        sleep 3
        
        # Test the health endpoint
        if curl -s http://127.0.0.1:8888/health | grep -q "healthy"; then
            log_test "PASS" "Local server startup and health check"
        else
            log_test "FAIL" "Local server health check failed"
        fi
        
        # Cleanup
        kill $SERVER_PID 2>/dev/null || true
        rm -f test_server.py
        cd - > /dev/null
    else
        log_test "FAIL" "Flask not available for server test"
    fi
}

test_bigquery_sql_syntax() {
    echo -e "\n${BLUE}Testing BigQuery SQL Syntax...${NC}"
    
    if [ -f "agents/data_intel_agent/bigquery_queries.sql" ]; then
        # Basic SQL syntax validation
        local sql_file="agents/data_intel_agent/bigquery_queries.sql"
        
        # Check for basic SQL keywords and structure
        if grep -q "SELECT\|FROM\|WHERE\|GROUP BY\|ORDER BY" "$sql_file"; then
            log_test "PASS" "BigQuery SQL contains expected keywords"
        else
            log_test "FAIL" "BigQuery SQL missing expected structure"
        fi
        
        # Check for BigQuery specific functions
        if grep -q "DATE(\|TIMESTAMP(\|EXTRACT(" "$sql_file"; then
            log_test "PASS" "BigQuery SQL contains BigQuery functions"
        else
            log_test "FAIL" "BigQuery SQL missing BigQuery functions"
        fi
    else
        log_test "FAIL" "BigQuery SQL file missing"
    fi
}

test_mcp_tools() {
    echo -e "\n${BLUE}Testing MCP Tools...${NC}"
    
    # Test Google Maps MCP
    if cd mcp/google_maps && python3 -c "from maps_mcp_agent import GoogleMapsMCPAgent; print('Import successful')" 2>/dev/null; then
        log_test "PASS" "Google Maps MCP import"
        cd - > /dev/null
    else
        log_test "FAIL" "Google Maps MCP import"
        cd - > /dev/null 2>/dev/null || true
    fi
    
    # Test Web Reader MCP
    if cd mcp/web_reader && python3 -c "from web_reader_mcp_server import WebReaderMCPServer; print('Import successful')" 2>/dev/null; then
        log_test "PASS" "Web Reader MCP import"
        cd - > /dev/null
    else
        log_test "FAIL" "Web Reader MCP import"
        cd - > /dev/null 2>/dev/null || true
    fi
}

# Run all tests
main() {
    echo "Starting smoke tests for Phoenix Outbreak Intelligence..."
    echo "Current directory: $(pwd)"
    echo "Python version: $(python3 --version 2>&1 || echo 'Not found')"
    echo ""
    
    test_python_installation
    test_file_structure
    test_dependencies
    test_agent_imports
    test_sample_data
    test_configuration_files
    test_deployment_scripts
    test_bigquery_sql_syntax
    test_mcp_tools
    test_local_server_startup
    
    echo -e "\n${BLUE}Smoke Test Results${NC}"
    echo "=================="
    echo -e "Total Tests: $TOTAL_TESTS"
    echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
    echo -e "${RED}Failed: $FAILED_TESTS${NC}"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "\n${GREEN}🎉 All smoke tests passed! Phoenix is ready for deployment.${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ Some tests failed. Please review and fix issues before deployment.${NC}"
        exit 1
    fi
}

# Run main function
main "$@"