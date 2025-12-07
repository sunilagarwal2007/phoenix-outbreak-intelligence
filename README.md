# 🦅 Phoenix Outbreak Intelligence

**AI-Powered Multi-Agent System for Early Outbreak Detection, Public Guidance & Rapid Response**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-ADK%20%7C%20BigQuery%20%7C%20Cloud%20Run-red.svg)](https://cloud.google.com)
## 📌 Project Summary

Phoenix Outbreak Intelligence is a multi-agent, real-time outbreak monitoring and crisis-response platform built using:

- **Google Agent Development Kit (ADK)**
- **BigQuery Public Health datasets** (COVID, Influenza, CDC, WHO)
- **MCP Tools** (Web reader, Google Maps)
- **A2A Remote Agent** (Cloud Run)
- **Vertex AI Agent Engine** for deployment

The system simulates how a Public Health Department would detect emerging outbreaks, assess risks, provide public guidance, and generate on-demand resource allocation reports.

### 🎯 Key Deliverables:
- ✔ **Early warning signals**
- ✔ **Rapid situational insights**
- ✔ **Misinformation detection**
- ✔ **Actionable public health guidance**
- ✔ **Reports for hospitals/emergency teams**
- ✔ **Multi-agent orchestration** with ADK, MCP & A2A

This project demonstrates deep integration with the Google Agentic AI ecosystem, providing a realistic and scalable solution for public health crisis management.

## 🚨 Problem Statement

Public health departments struggle with:

### ❗ Rapidly identifying early outbreak signals

Data comes from multiple fragmented sources:
- CDC datasets
- Hospital admissions  
- Lab test positivity
- Social chatter & misinformation
- News reports

### ❗ High manual workload in triaging signals

Analysts must manually:
- Pull spreadsheets
- Check hospital loads
- Compare regions
- Validate rumors
- Prepare public advisories

### ❗ Slow response → delayed interventions

**Delayed detection** = 
- ➡ spread accelerates
- ➡ hospital strain increases  
- ➡ misinformation spreads
- ➡ public confusion rises

## 🎯 Solution: Phoenix Outbreak Intelligence

A multi-agent AI system that automates:

### 📊 Data Intelligence & Risk Scoring (Data Intelligence Agent)
- Queries BigQuery public datasets
- Detects abnormal spikes
- Computes outbreak likelihood
- Runs trend, positivity & hospital strain analysis
- Validates online rumors via MCP Web Reader

### 🛡️ Public Safety & Guidance (Public Guidance Agent)
Converts findings into simple, trusted advice:
- Mask guidance
- School safety recommendations
- Travel advisory
- Symptom checklist

### 🏥 Resource & Infrastructure Planning (A2A Agent on Cloud Run)
- Generates PDF reports
- Computes resource shortages
- Suggests ICU beds, PPE, testing center expansions
- Uses Google Maps MCP for routing / hotspot mapping

### 🎛️ Orchestrator Agent
- Coordinates all agents
- Routes requests
- Combines outputs into final intelligence briefing

## 💡 Why Phoenix Outbreak Intelligence?

This project addresses critical public health challenges with advanced AI capabilities:

### ✔ **Technical Innovation**
Multi-agent architecture combining ADK, MCP, A2A, BigQuery, and Cloud Run

### ✔ **Real-World Impact**
Helps public health departments detect outbreaks faster and respond more effectively

### ✔ **Production-Ready Features**
- Real-time BigQuery data analysis
- Interactive maps and visualizations
- Automated rumor validation
- Risk scoring and trend analysis
- Actionable public health guidance
- Resource allocation reports

### ✔ **Full Google AI Ecosystem Integration**
- Agent Development Kit (ADK)
- Model Context Protocol (MCP) Tools
- Vertex AI Agent Engine
- Cloud Run deployment
- BigQuery public datasets
- Gemini AI models

## 🏗 System Architecture (High Level)

```

┌───────────────────────────────────────────────┐
│ 👤 USER QUERY                                 │
│ “Is there an outbreak in California today?”   │
└───────────────────────────────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────────┐
│ 🎯 PHOENIX ORCHESTRATOR (ADK Agent)           │
│ • Intent understanding (Gemini)               │
│ • Query routing                               │
│ • Multi-agent coordination                    │
└───────────────────────────────────────────────┘
   │                    │                    │                     │
   ▼                    ▼                    ▼                     ▼
┌─────────────┐   ┌────────────────┐  ┌────────────────┐   ┌────────────────┐
│ 📊 Data      │   │ 🛡 Public       │  │ 📄 A2A Report    │   │ 🔧 MCP Tools    │
│ Intel Agent │   │ Guidance Agent │  │ Agent (CloudRun) │   │ Web + Maps APIs │
└─────────────┘   └────────────────┘  └────────────────┘   └────────────────┘
   │                    │                    │                     │
   ▼                    ▼                    ▼                     ▼
BigQuery SQL       Safety Advice        PDF / JSON Report     Web Reader / Maps
Outbreak Data      Rumor Check          Cloud Run A2A         Verified Context
```



## 📁 Project Structure

```
phoenix-outbreak-intelligence/
├── README.md
├── requirements.txt
├── agents/                              # Multi-agent system components
│   ├── data_intel_agent/               # BigQuery analysis & risk scoring
│   ├── public_guidance_agent/          # Health recommendations
│   ├── resource_report_agent_A2A/      # Resource allocation (Cloud Run)
│   └── orchestrator/                   # Main coordinator
├── mcp/                                # Model Context Protocol tools
│   ├── google_maps/                   # Location & mapping services
│   └── web_reader/                     # Web scraping & validation
├── data/                               # Sample datasets
│   ├── sample_api_outputs/
│   └── sample_bigquery_results/
├── deployment/                         # Deployment scripts
├── tests/                              # Testing suite
```

## ⚙️ Key Features

### 1️⃣ **Outbreak Risk Detection** (BigQuery + ADK Tools)
- 📈 Daily case + positivity + hospitalization trends
- 📊 Multi-day moving averages
- ⚡ Acceleration index (growth rate)
- 🎯 Outbreak probability scoring (0–100)

### 2️⃣ **Misinformation & Rumor Validation** (MCP Web Reader)
- 🌐 Scrapes public web sources
- 📝 Extracts claims
- ✅ Validates against official datasets

### 3️⃣ **Public Safety Guidance** (Gemini)
- 📍 Region-specific recommendations
- 🏫 School, travel, workplace guidance
- 📋 Risk-level narratives

### 4️⃣ **Resource Allocation Report** (A2A Remote Agent)
- ☁️ Cloud Run microservice
- 🧮 Calculates PPE, testing, ICU forecast
- 📄 Generates PDF report

### 5️⃣ **Orchestrator for Unified Experience**
- 🎯 Intent classification
- 🔄 Manages multi-agent workflow
- 🔗 Combines all outputs into final insights

## 🚀 Deployment

### 🌐 **Quick Deploy to Google Cloud Run**

Deploy the complete Flask web application with one command:

```bash
# Set your GCP project
export PROJECT_ID="your-gcp-project-id"

# Run deployment script
./deploy.sh
```

This script will:
1. Enable required GCP APIs (Cloud Run, Cloud Build, BigQuery, Vertex AI)
2. Build Docker container image
3. Deploy to Cloud Run (us-central1)
4. Configure auto-scaling and health checks
5. Provide you with a public HTTPS URL

**Deployment time:** ~5-10 minutes

**Result:** Your app will be live at `https://phoenix-webapp-[hash]-uc.a.run.app`

### 🛠️ **Advanced Deployment Options**

**Deploy Individual Agents as Microservices:**
```bash
cd deployment
export PROJECT_ID="your-gcp-project-id"
./deploy_cloud_run.sh
```

Deploys:
- Data Intelligence Agent
- Public Guidance Agent (with MCP)
- Resource Report Agent (A2A)
- Orchestrator
- MCP Services (Web Reader, Google Maps)

**Deploy to Vertex AI Agent Engine:**
```bash
cd deployment
export PROJECT_ID="your-gcp-project-id"
./deploy_agent_engine.sh
```

Features:
- Native Vertex AI agent integration
- Human-in-the-loop workflows
- Advanced conversation management

### 💻 **Local Development**

Run locally for testing:
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PROJECT_ID="your-gcp-project-id"
export PORT=5002

# Run Flask app
python flask_app.py
```

Access at: `http://localhost:5002`

## 🧪 Testing

### 😁 **Quick Smoke Test**
```bash
bash tests/smoke_test.sh
```

### 🔍 **Integration Testing**
```bash
python3 tests/integration_test.py
```

### 📊 **Demo Test Cases**
Check out `tests/demo_chat_cases.json` for pre-built conversation flows and test scenarios.

---

## 🛠️ Getting Started

### Prerequisites
- Python 3.8+
- Google Cloud SDK
- ADK CLI installed
- BigQuery access

### Quick Setup

**1. Clone the repository:**
```bash
git clone https://github.com/sunilagarwal2007/phoenix-outbreak-intelligence.git
cd phoenix-outbreak-intelligence
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Set up Google Cloud credentials:**
```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud auth application-default login

# Set your project
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID
```

**4. Deploy to Cloud Run (recommended):**
```bash
./deploy.sh
```

**OR run locally for development:**
```bash
export PROJECT_ID="your-gcp-project-id"
export PORT=5002
python flask_app.py
```

Access at: `http://localhost:5002`

### Environment Variables

Required:
```bash
export PROJECT_ID="your-gcp-project-id"          # GCP project ID
```

Optional:
```bash
export PORT=5002                                  # Local development port
export GOOGLE_MAPS_API_KEY="your-api-key"       # For full Maps MCP features
export REGION="us-central1"                      # GCP region for deployment
```
---

## 🎬 Screenshot

<img width="1208" height="866" alt="image" src="https://github.com/user-attachments/assets/b447a900-6864-4edb-a29e-0946e17c92e8" />

Question: What is the COVID-19 risk level in California?

<img width="1209" height="1431" alt="screencapture-phoenix-webapp-197" src="https://github.com/user-attachments/assets/8362bb0b-1cf1-42cf-b447-e8d593890be8" />

Question: Should I cancel my family gathering this weekend?
<img width="1199" height="1082" alt="screencapture-phoenix-webapp-197666350447-us-central1-run-app-2025-12-07-12_51_49" src="https://github.com/user-attachments/assets/4463e28a-2f93-4849-ad51-27546e5af0b5" />

Question: I got fever , What should I do ?
<img width="827" height="1650" alt="screencapture-phoenix-webapp-1971" src="https://github.com/user-attachments/assets/a129a9f1-b38b-4df4-a1a6-f10f28f3a898" />


---

## 🎬 Live Demo

**Try the deployed application:**

🌐 **Live URL:** [Access Phoenix Outbreak Intelligence](https://phoenix-webapp-197666350447.us-central1.run.app/)

**Sample queries to try:**
1. "Is there an outbreak in California?"
2. "I heard a rumor about a new variant in Mumbai with 60% fatality. Is it true?"
3. "I have fever and cough in San Francisco. Where should I go?"
4. "What healthcare resources are needed in Los Angeles?"

**Features you'll see:**
- Real-time BigQuery data analysis
- MCP-powered rumor validation
- Healthcare facility finder with Google Maps
- Risk scoring and trend visualization
- Actionable public health guidance

---


**🎆 Ready to detect the next outbreak before it spreads? Let Phoenix rise to the challenge!**
