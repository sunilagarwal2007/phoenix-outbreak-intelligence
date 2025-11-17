#!/usr/bin/env python3
"""
Flask Web App for Phoenix Outbreak Intelligence
Simple Q&A interface for outbreak risk analysis
"""

from flask import Flask, render_template, request, jsonify
import os
import sys
import asyncio
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import agents
from agents.data_intel_agent.agent import DataIntelligenceAgent
from agents.public_guidance_agent.agent import PublicGuidanceAgent
from agents.resource_report_agent_A2A.agent import ResourceReportAgent
from agents.orchestrator.router import PhoenixRouter
from agents.orchestrator.workflow import PhoenixWorkflow

app = Flask(__name__)

# Initialize agents
PROJECT_ID = os.getenv('PROJECT_ID', 'qwiklabs-gcp-03-e96cc2da1c33')
data_agent = DataIntelligenceAgent(project_id=PROJECT_ID)
guidance_agent = PublicGuidanceAgent(project_id=PROJECT_ID)
resource_agent = ResourceReportAgent(project_id=PROJECT_ID)
router = PhoenixRouter()
workflow = PhoenixWorkflow(data_agent, guidance_agent, resource_agent)

# Sample questions
SAMPLE_QUESTIONS = [
    "What is the COVID-19 risk level in California?",
    "Compare risk between California, Texas, and New York",
    "Should I cancel my family gathering this weekend?",
    "Do we have enough ICU beds in California?",
    "What PPE should healthcare workers use?",
    "Give me a complete outbreak briefing for California"
]


@app.route('/')
def home():
    """Home page with Q&A interface"""
    return render_template('index.html', sample_questions=SAMPLE_QUESTIONS)


@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Handle question from user"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Please provide a question'}), 400
        
        # Route question to appropriate agent(s)
        response = asyncio.run(process_question(question))
        
        return jsonify({
            'question': question,
            'answer': response['answer'],
            'agent': response['agent'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


async def process_question(question: str) -> dict:
    """Process question and route to appropriate agent"""
    
    question_lower = question.lower()
    location = extract_location(question)
    
    # Check for rumor/misinformation validation
    if any(word in question_lower for word in ['heard', 'rumor', 'whatsapp', 'facebook', 'true', 'fake', 'hoax', 'misinformation', 'claim']):
        # This is a rumor validation question
        answer = await handle_rumor_question(question, location)
        return {'answer': answer, 'agent': 'Public Guidance Agent (Rumor Validation)'}
    
    # Check for personal health symptoms
    if any(word in question_lower for word in ['fever', 'cough', 'sick', 'symptoms', 'ill', 'headache', 'sore throat', 'shortness of breath']):
        # Personal health guidance
        answer = await handle_health_symptom_question(question, location)
        return {'answer': answer, 'agent': 'Public Guidance Agent (Health Guidance)'}
    
    # Check for orchestrator keywords (comprehensive briefing)
    if any(word in question_lower for word in ['complete', 'full', 'briefing', 'comprehensive', 'everything']):
        # Use workflow for multi-agent response
        result = await workflow.execute_full_analysis(
            location=location,
            target_audience="general_public",
            generate_pdf=False
        )
        
        # Format comprehensive response
        answer = "# Complete Outbreak Intelligence Briefing\n\n"
        
        if 'risk_analysis' in result:
            data = result['risk_analysis']
            answer += f"## 📊 Epidemiological Analysis\n\n"
            answer += f"**Risk Score:** {data.get('risk_score', 'N/A')}/100 - {data.get('risk_level', 'N/A')}\n\n"
            if 'trends' in data:
                trends = data['trends']
                answer += f"**Trends:**\n"
                answer += f"- Case Trend: {trends.get('case_trend', 'N/A')}\n"
                answer += f"- Growth Rate: {trends.get('growth_rate', 'N/A')}%\n"
                answer += f"- Daily Cases: {trends.get('cases_7day_avg', 'N/A')}\n"
                answer += f"- ICU Occupancy: {trends.get('icu_occupancy', 'N/A')}%\n\n"
        
        if 'guidance_results' in result:
            guidance = result['guidance_results']
            answer += f"## 🎯 Public Health Guidance\n\n"
            answer += f"**Alert Level:** {guidance.get('alert_level', 'N/A')}\n\n"
            if 'public_message' in guidance:
                msg = guidance['public_message']
                answer += f"**{msg.get('headline', 'Important Update')}**\n\n"
                if 'key_actions' in msg:
                    answer += "**Key Actions:**\n"
                    for action in msg['key_actions']:
                        answer += f"- {action}\n"
                answer += "\n"
        
        if 'resource_report' in result:
            resources = result['resource_report']
            answer += f"## 🏥 Resource Analysis\n\n"
            if 'resource_needs' in resources and 'icu_beds' in resources['resource_needs']:
                icu = resources['resource_needs']['icu_beds']
                answer += f"**ICU Capacity:**\n"
                answer += f"- Current: {icu.get('current_capacity', 'N/A')} beds\n"
                answer += f"- Projected Need: {icu.get('projected_need', 'N/A')} beds\n"
                answer += f"- Deficit: {icu.get('deficit', 'N/A')} beds\n"
                answer += f"- Status: {icu.get('recommendation', 'N/A')}\n\n"
        
        return {'answer': answer, 'agent': 'Phoenix Workflow (Multi-Agent)'}
    
    # Check for data/risk analysis keywords
    elif any(word in question_lower for word in ['risk', 'cases', 'trend', 'data', 'analysis', 'compare', 'statistics']):
        result = await data_agent.analyze_outbreak_risk(
            location=extract_location(question),
            days_back=14
        )
        
        answer = format_risk_analysis(result)
        return {'answer': answer, 'agent': 'Data Intelligence Agent'}
    
    # Check for specific activity questions (gathering, travel, etc)
    elif any(word in question_lower for word in ['gathering', 'party', 'wedding', 'event', 'meeting', 'cancel', 'postpone']):
        # Gathering/event specific guidance
        answer = await handle_gathering_question(question, location)
        return {'answer': answer, 'agent': 'Public Guidance Agent (Event Planning)'}
    
    # Check for travel questions
    elif any(word in question_lower for word in ['travel', 'trip', 'flight', 'visit', 'vacation', 'safe to go']):
        # Travel specific guidance
        answer = await handle_travel_question(question, location)
        return {'answer': answer, 'agent': 'Public Guidance Agent (Travel Advisory)'}
    
    # Check for general guidance keywords
    elif any(word in question_lower for word in ['should', 'guidance', 'advice', 'recommendation', 'safe', 'protect']):
        # First get risk analysis
        location = extract_location(question)
        risk_result = await data_agent.analyze_outbreak_risk(location=location, days_back=14)
        
        result = await guidance_agent.generate_public_guidance(
            risk_analysis=risk_result,
            location=location,
            target_audience='general_public'
        )
        
        answer = format_guidance(result)
        return {'answer': answer, 'agent': 'Public Guidance Agent'}
    
    # Check for resource keywords
    elif any(word in question_lower for word in ['resource', 'capacity', 'beds', 'icu', 'ventilator', 'hospital', 'supply', 'equipment']):
        # First get risk analysis
        location = extract_location(question)
        risk_result = await data_agent.analyze_outbreak_risk(location=location, days_back=14)
        
        result = await resource_agent.generate_resource_report(
            risk_analysis=risk_result,
            location=location,
            forecast_days=14
        )
        
        answer = format_resource_report(result)
        return {'answer': answer, 'agent': 'Resource Report Agent'}
    
    # Default: Use data intelligence agent
    else:
        result = await data_agent.analyze_outbreak_risk(
            location=extract_location(question),
            days_back=14
        )
        answer = format_risk_analysis(result)
        return {'answer': answer, 'agent': 'Data Intelligence Agent (Default)'}


async def handle_rumor_question(question: str, location: str) -> str:
    """Handle rumor validation questions using MCP Web Reader"""
    answer = f"# 🔍 Rumor Verification (MCP-Powered)\n\n"
    answer += f"**Your Question:** {question}\n\n"
    
    # Extract the claim from the question
    claim = question
    if "heard" in question.lower():
        # Try to extract just the claim part
        parts = question.lower().split("heard")
        if len(parts) > 1:
            claim = parts[1].strip().rstrip("?.")
    
    # Use MCP Web Reader to validate the claim
    try:
        validation = await guidance_agent.validate_rumor_with_mcp(claim, location)
        
        verdict = validation.get("verdict", "UNVERIFIED")
        confidence = validation.get("confidence", 0.0)
        explanation = validation.get("explanation", "No explanation available")
        sources = validation.get("sources", [])
        
        # Display verdict with emoji
        verdict_emoji = {
            "CONFIRMED": "✅",
            "FALSE": "❌",
            "PARTIALLY_VERIFIED": "⚠️",
            "INVESTIGATING": "🔍",
            "UNVERIFIED": "❓",
            "ERROR": "⚠️"
        }
        
        answer += f"## {verdict_emoji.get(verdict, '❓')} Verdict: {verdict}\n\n"
        answer += f"**Confidence:** {confidence * 100:.0f}%\n\n"
        answer += f"### 📋 Analysis:\n{explanation}\n\n"
        
        if sources:
            answer += "### 📚 Verified Sources:\n"
            for source in sources[:5]:
                answer += f"- {source}\n"
            answer += "\n"
        
    except Exception as e:
        answer += f"## ⚠️ Unable to Validate\n\n"
        answer += f"MCP validation unavailable: {str(e)}\n\n"
        
        # Fallback analysis
        if "fatality" in question.lower() or "death rate" in question.lower():
            answer += "### ⚠️ Assessment: LIKELY MISINFORMATION\n\n"
            answer += "**Red Flags Identified:**\n"
            answer += "- Extreme claims (e.g., 60% fatality) without official sources\n"
            answer += "- Information from social media/messaging apps\n"
            answer += "- No citation of health authorities (WHO, CDC)\n\n"
    
    answer += "## 🛡️ Safe Next Steps:\n\n"
    answer += "1. **DO NOT share** unverified information - it can cause panic\n"
    answer += "2. **Check official sources** before believing health claims\n"
    answer += "3. **Be skeptical** of extreme statistics without sources\n"
    answer += "4. **Report misinformation** to platform moderators\n"
    answer += "5. **Follow verified accounts** of health organizations\n\n"
    
    answer += "## 📞 Trusted Sources:\n\n"
    answer += "- **WHO:** https://www.who.int\n"
    answer += "- **CDC:** https://www.cdc.gov\n"
    answer += f"- **{location} Health Dept:** Contact via official website\n"
    answer += "- **Local News:** Established media with health reporters\n\n"
    
    answer += "*✨ Powered by MCP Web Reader for real-time fact-checking*"
    
    return answer


async def handle_health_symptom_question(question: str, location: str) -> str:
    """Handle personal health symptom questions"""
    answer = f"# 🩺 Health Guidance\n\n"
    answer += f"**Your Concern:** {question}\n\n"
    
    # Identify symptoms mentioned
    symptoms = []
    if "fever" in question.lower():
        symptoms.append("fever")
    if "cough" in question.lower():
        symptoms.append("cough")
    if "sore throat" in question.lower():
        symptoms.append("sore throat")
    if "headache" in question.lower():
        symptoms.append("headache")
    
    answer += "## ⚠️ Important Disclaimer\n\n"
    answer += "**I am NOT a doctor and cannot provide medical diagnosis.** "
    answer += "The following is general public health guidance only.\n\n"
    
    answer += "## 🏠 Immediate Self-Care Steps:\n\n"
    
    if symptoms:
        answer += f"**For your symptoms ({', '.join(symptoms)}):**\n\n"
    
    answer += "1. **Stay Home & Rest**\n"
    answer += "   - Isolate from others in your household\n"
    answer += "   - Rest and drink plenty of fluids\n"
    answer += "   - Monitor your temperature regularly\n\n"
    
    answer += "2. **Over-the-Counter Care**\n"
    answer += "   - Acetaminophen (Tylenol) or ibuprofen (Advil) for fever\n"
    answer += "   - Follow dosage instructions on packaging\n"
    answer += "   - Stay hydrated with water, tea, or broth\n\n"
    
    answer += "3. **Monitor Symptoms**\n"
    answer += "   - Track temperature every 4-6 hours\n"
    answer += "   - Note any new or worsening symptoms\n"
    answer += "   - Keep a symptom diary\n\n"
    
    answer += "## 🚨 When to Seek Medical Care IMMEDIATELY:\n\n"
    answer += "Call 911 or go to ER if you experience:\n"
    answer += "- ❌ Difficulty breathing or shortness of breath\n"
    answer += "- ❌ Persistent chest pain or pressure\n"
    answer += "- ❌ Confusion or inability to stay awake\n"
    answer += "- ❌ Bluish lips or face\n"
    answer += "- ❌ High fever (>103°F/39.4°C) not responding to medication\n\n"
    
    answer += "## 📞 When to Call Your Doctor:\n\n"
    answer += "Contact your healthcare provider if:\n"
    answer += "- Symptoms last more than 3-5 days\n"
    answer += "- Fever doesn't improve with medication\n"
    answer += "- You have underlying health conditions\n"
    answer += "- You're pregnant or immunocompromised\n"
    answer += "- You're concerned about your symptoms\n\n"
    
    answer += "## 🧪 Testing:\n\n"
    answer += "- Consider getting tested for COVID-19, flu, and strep throat\n"
    
    # Use MCP Google Maps to find nearby testing/healthcare facilities
    try:
        facilities = await guidance_agent.find_nearby_facilities_with_mcp(
            location=location,
            facility_type="hospital",
            radius=10000  # 10km radius
        )
        
        if facilities and len(facilities) > 0:
            answer += f"\n### 🗺️ Nearby Healthcare Facilities (via MCP Google Maps):\n\n"
            for i, facility in enumerate(facilities[:3], 1):  # Show top 3
                answer += f"{i}. **{facility.get('name', 'N/A')}**\n"
                answer += f"   - Address: {facility.get('address', 'N/A')}\n"
                if 'phone' in facility:
                    answer += f"   - Phone: {facility.get('phone', 'N/A')}\n"
                if 'distance' in facility:
                    answer += f"   - Distance: {facility.get('distance', 'N/A')}\n"
                answer += "\n"
        else:
            answer += f"- Find testing locations in {location} via:\n"
            answer += "  - Local health department website\n"
            answer += "  - Urgent care clinics\n"
            answer += "  - Pharmacy testing services\n"
    except Exception as e:
        answer += f"- Find testing locations in {location} via:\n"
        answer += "  - Local health department website\n"
        answer += "  - Urgent care clinics\n"
        answer += "  - Pharmacy testing services\n"
    
    answer += "\n## 🏥 Additional Resources:\n\n"
    answer += f"- **{location} Health Dept:** Check official website for hotline\n"
    answer += "- **Nurse Hotline:** Many insurers offer 24/7 nurse advice\n"
    answer += "- **Telehealth:** Consider virtual doctor visit\n"
    answer += "- **Emergency:** 911\n\n"
    
    answer += "*✨ Healthcare facility finder powered by MCP Google Maps*\n"
    answer += "*Take care of yourself and don't hesitate to seek help if symptoms worsen!*"
    
    return answer


async def handle_gathering_question(question: str, location: str) -> str:
    """Handle questions about gatherings and events"""
    # Get risk analysis first
    risk_result = await data_agent.analyze_outbreak_risk(location=location, days_back=14)
    risk_level = risk_result.get('risk_level', 'MODERATE')
    risk_score = risk_result.get('risk_score', 50)
    
    answer = f"# 🎉 Event Planning Guidance\n\n"
    answer += f"**Your Question:** {question}\n\n"
    answer += f"**Current Risk Level in {location}:** {risk_level} ({risk_score}/100)\n\n"
    
    # Risk-based recommendation
    if risk_level == "CRITICAL":
        answer += "## 🚨 Recommendation: POSTPONE\n\n"
        answer += "**Given the CRITICAL risk level, we strongly recommend postponing large gatherings.**\n\n"
        answer += "### Why:\n"
        answer += "- Very high community transmission\n"
        answer += "- Healthcare system under strain\n"
        answer += "- Risk of outbreak at gathering is significant\n\n"
        
        answer += "### Alternatives:\n"
        answer += "- **Virtual celebration** via Zoom, FaceTime, or other video platforms\n"
        answer += "- **Postpone** to a later date when risk decreases\n"
        answer += "- **Outdoor small gathering** (max 5-10 people) with masks and distance\n"
        answer += "- **Drive-by celebration** or outdoor drop-in with precautions\n\n"
        
    elif risk_level == "HIGH":
        answer += "## ⚠️ Recommendation: MODIFY or POSTPONE\n\n"
        answer += "**Consider significantly modifying your gathering or postponing.**\n\n"
        answer += "### If You Must Proceed:\n"
        answer += "1. **Move outdoors** - significantly reduces transmission risk\n"
        answer += "2. **Limit guest list** - keep to immediate family/close contacts only\n"
        answer += "3. **Require masks** indoors and when close together\n"
        answer += "4. **Check vaccination status** of all attendees\n"
        answer += "5. **Ask guests to test** before attending (rapid test day-of)\n"
        answer += "6. **Provide hand sanitizer** and encourage frequent handwashing\n"
        answer += "7. **Improve ventilation** - open windows, use fans\n"
        answer += "8. **Keep it short** - 2-3 hours maximum\n\n"
        
    elif risk_level == "MODERATE":
        answer += "## 🔶 Recommendation: PROCEED WITH CAUTION\n\n"
        answer += "**You can proceed, but take enhanced precautions.**\n\n"
        answer += "### Recommended Safety Measures:\n"
        answer += "1. **Prefer outdoors** if weather permits\n"
        answer += "2. **Limit capacity** - don't overcrowd the space\n"
        answer += "3. **Masks available** for guests who want them\n"
        answer += "4. **Good ventilation** - open windows if indoors\n"
        answer += "5. **Request testing** for symptomatic guests only\n"
        answer += "6. **Hand hygiene** - soap and sanitizer readily available\n"
        answer += "7. **Monitor symptoms** - guests should stay home if unwell\n\n"
        
    else:
        answer += "## ✅ Recommendation: PROCEED WITH STANDARD PRECAUTIONS\n\n"
        answer += "**Current risk is low. You can have your gathering with basic precautions.**\n\n"
        answer += "### Basic Precautions:\n"
        answer += "1. **Ask guests** to stay home if they feel unwell\n"
        answer += "2. **Have hand sanitizer** available\n"
        answer += "3. **Clean frequently** touched surfaces\n"
        answer += "4. **Ventilate** the space well\n"
        answer += "5. **Be respectful** if some guests choose to wear masks\n\n"
    
    answer += "## 🤔 Consider These Factors:\n\n"
    answer += "- **Vulnerable guests?** (elderly, immunocompromised, pregnant)\n"
    answer += "- **Guest travel distance?** (local vs. coming from other states)\n"
    answer += "- **Indoor or outdoor?** (outdoor is much safer)\n"
    answer += "- **Guest count?** (smaller is safer)\n"
    answer += "- **Duration?** (shorter is safer)\n\n"
    
    answer += "## 📝 Communicate With Guests:\n\n"
    answer += "- Share your safety plan in advance\n"
    answer += "- Let guests make their own comfort-level decisions\n"
    answer += "- Respect those who choose not to attend\n"
    answer += "- Provide masks for guests who want them\n\n"
    
    answer += f"*Check {location} health department for any specific local guidance or restrictions.*"
    
    return answer


async def handle_travel_question(question: str, location: str) -> str:
    """Handle travel-related questions"""
    # Get risk analysis for destination
    risk_result = await data_agent.analyze_outbreak_risk(location=location, days_back=14)
    risk_level = risk_result.get('risk_level', 'MODERATE')
    risk_score = risk_result.get('risk_score', 50)
    
    answer = f"# ✈️ Travel Advisory\n\n"
    answer += f"**Your Question:** {question}\n\n"
    answer += f"**Destination: {location}**\n"
    answer += f"**Current Risk Level:** {risk_level} ({risk_score}/100)\n\n"
    
    # Risk-based travel advice
    if risk_level == "CRITICAL":
        answer += "## 🚨 Travel Advisory: AVOID NON-ESSENTIAL TRAVEL\n\n"
        answer += f"**We recommend avoiding non-essential travel to {location} at this time.**\n\n"
        answer += "### Reasons:\n"
        answer += "- Very high community transmission\n"
        answer += "- Healthcare system potentially overwhelmed\n"
        answer += "- Significant risk of exposure and illness\n\n"
        
        answer += "### If Travel is Essential:\n"
        answer += "1. **Get tested** before and after travel\n"
        answer += "2. **Wear N95/KN95 mask** in all indoor public spaces\n"
        answer += "3. **Avoid crowded areas** and indoor dining\n"
        answer += "4. **Have isolation plan** in case you become ill\n"
        answer += "5. **Know where to get medical care** at destination\n"
        answer += "6. **Have travel insurance** that covers illness\n\n"
        
    elif risk_level == "HIGH":
        answer += "## ⚠️ Travel Advisory: RECONSIDER TRAVEL\n\n"
        answer += f"**Consider postponing non-essential travel to {location}.**\n\n"
        answer += "### If You Must Travel:\n"
        answer += "1. **Get vaccinated and boosted** before travel\n"
        answer += "2. **Mask in transit** - planes, trains, buses, airports\n"
        answer += "3. **Test before travel** (day-of or day before)\n"
        answer += "4. **Choose outdoor activities** when possible\n"
        answer += "5. **Avoid large indoor gatherings**\n"
        answer += "6. **Bring rapid tests** for use during trip\n"
        answer += "7. **Have contingency plans** if you test positive while traveling\n\n"
        
    elif risk_level == "MODERATE":
        answer += "## 🔶 Travel Advisory: EXERCISE CAUTION\n\n"
        answer += f"**Travel to {location} is possible with reasonable precautions.**\n\n"
        answer += "### Recommended Precautions:\n"
        answer += "1. **Wear masks** in crowded indoor spaces\n"
        answer += "2. **Test if symptomatic** during or after trip\n"
        answer += "3. **Choose outdoor activities** when possible\n"
        answer += "4. **Practice good hygiene** - wash hands frequently\n"
        answer += "5. **Stay informed** about local conditions\n"
        answer += "6. **Have health insurance** active at destination\n\n"
        
    else:
        answer += "## ✅ Travel Advisory: NORMAL PRECAUTIONS\n\n"
        answer += f"**Travel to {location} is currently low risk.**\n\n"
        answer += "### Standard Travel Health Tips:\n"
        answer += "1. **Pack masks** in case local conditions change\n"
        answer += "2. **Stay home if sick** before or during travel\n"
        answer += "3. **Practice good hygiene**\n"
        answer += "4. **Know local healthcare options**\n"
        answer += "5. **Monitor your health** during and after travel\n\n"
    
    answer += "## 🧳 Travel Health Checklist:\n\n"
    answer += "### Before You Go:\n"
    answer += "- [ ] Check current conditions at destination\n"
    answer += "- [ ] Verify travel insurance coverage\n"
    answer += "- [ ] Pack masks, hand sanitizer, rapid tests\n"
    answer += "- [ ] Note local health department contact info\n"
    answer += "- [ ] Ensure vaccinations up to date\n"
    answer += "- [ ] Download local health apps if available\n\n"
    
    answer += "### During Travel:\n"
    answer += "- [ ] Mask in transit (planes, trains, buses)\n"
    answer += "- [ ] Choose outdoor venues when possible\n"
    answer += "- [ ] Maintain good hand hygiene\n"
    answer += "- [ ] Avoid obviously sick people\n"
    answer += "- [ ] Keep track of places visited (for contact tracing)\n\n"
    
    answer += "### After Travel:\n"
    answer += "- [ ] Monitor for symptoms 5-14 days post-travel\n"
    answer += "- [ ] Test if you develop symptoms\n"
    answer += "- [ ] Follow local quarantine guidance if applicable\n"
    answer += "- [ ] Inform close contacts if you test positive\n\n"
    
    answer += f"## 🌐 Resources:\n\n"
    answer += f"- **{location} Health Dept:** Check official website\n"
    answer += "- **CDC Travel Health:** https://wwwnc.cdc.gov/travel\n"
    answer += "- **Local Testing Sites:** Search on arrival\n"
    answer += "- **Emergency Services:** 911\n\n"
    
    answer += "*Travel conditions can change rapidly. Check for updates before departure!*"
    
    return answer


def extract_location(question: str) -> str:
    """Extract location from question"""
    question_lower = question.lower()
    
    # Common state names
    states = {
        'california': 'California',
        'ca': 'California',
        'texas': 'Texas',
        'tx': 'Texas',
        'new york': 'New York',
        'ny': 'New York',
        'florida': 'Florida',
        'fl': 'Florida',
        'mumbai': 'Mumbai',
        'delhi': 'Delhi',
        'india': 'India'
    }
    
    for key, value in states.items():
        if key in question_lower:
            return value
    
    return 'California'  # Default


def format_risk_analysis(result: dict) -> str:
    """Format risk analysis result"""
    answer = f"# 📊 Risk Analysis\n\n"
    answer += f"**Risk Score:** {result.get('risk_score', 'N/A')}/100\n"
    answer += f"**Risk Level:** {result.get('risk_level', 'N/A')}\n"
    answer += f"**Confidence:** {result.get('confidence', 'N/A')}%\n\n"
    
    if 'trends' in result:
        trends = result['trends']
        
        # Case trends
        if 'cases' in trends and trends['cases']:
            cases = trends['cases']
            answer += "## 📈 Case Trends\n\n"
            answer += f"- **Latest Daily Cases:** {cases.get('latest_count', 'N/A'):,}\n"
            answer += f"- **7-Day Average:** {cases.get('seven_day_average', 'N/A'):,.0f}\n"
            answer += f"- **Growth Rate:** {cases.get('growth_rate', 0) * 100:.1f}% week-over-week\n"
            answer += f"- **Trend:** {cases.get('trend', 'N/A')}\n\n"
        
        # Positivity rates
        if 'positivity' in trends and trends['positivity']:
            pos = trends['positivity']
            answer += "## 🧪 Test Positivity\n\n"
            answer += f"- **Current Rate:** {pos.get('latest_rate', 0) * 100:.1f}%\n"
            answer += f"- **Average Rate:** {pos.get('average_rate', 0) * 100:.1f}%\n\n"
        
        # Hospital capacity
        if 'hospitals' in trends and trends['hospitals']:
            hosp = trends['hospitals']
            answer += "## 🏥 Hospital Capacity\n\n"
            answer += f"- **ICU Occupancy:** {hosp.get('icu_occupancy', 0) * 100:.1f}%\n"
            answer += f"- **Total ICU Beds:** {hosp.get('total_icu_beds', 'N/A'):,}\n"
            answer += f"- **Occupied Beds:** {hosp.get('occupied_beds', 'N/A'):,}\n"
            answer += f"- **Available Beds:** {hosp.get('available_beds', 'N/A'):,}\n"
            answer += f"- **Status:** {hosp.get('utilization_trend', 'N/A')}\n\n"
    
    if 'insights' in result and result['insights']:
        answer += "## 💡 Key Insights\n\n"
        for idx, insight in enumerate(result['insights'][:5], 1):
            answer += f"{idx}. {insight}\n"
        answer += "\n"
    
    answer += f"\n*Note: Data represents realistic outbreak patterns based on historical public health data (2020-2022).*"
    
    return answer


def format_guidance(result: dict) -> str:
    """Format public guidance result"""
    answer = f"# 🎯 Public Health Guidance\n\n"
    
    # Risk context
    if 'risk_context' in result:
        risk = result['risk_context']
        answer += f"**Risk Level:** {risk.get('risk_level', 'N/A')}\n"
        answer += f"**Risk Score:** {risk.get('risk_score', 'N/A')}/100\n\n"
    
    # Location and audience
    answer += f"**Location:** {result.get('location', 'N/A')}\n"
    answer += f"**Target Audience:** {result.get('target_audience', 'general_public').replace('_', ' ').title()}\n\n"
    
    # Key recommendations
    if 'key_recommendations' in result and result['key_recommendations']:
        answer += "## 📋 Key Recommendations\n\n"
        for rec in result['key_recommendations']:
            answer += f"{rec}\n\n"
    
    # Category-specific guidance
    if 'guidance_categories' in result:
        answer += "## 📚 Detailed Guidance by Category\n\n"
        categories = result['guidance_categories']
        
        # Extract guidance from GuidanceRecommendation objects or dicts
        for category, guidance_obj in categories.items():
            if hasattr(guidance_obj, 'recommendation'):
                recommendation = guidance_obj.recommendation
                severity = guidance_obj.severity_level
            elif isinstance(guidance_obj, dict):
                recommendation = guidance_obj.get('recommendation', 'N/A')
                severity = guidance_obj.get('severity_level', 'N/A')
            else:
                continue
                
            icon = {
                'masking': '😷',
                'travel': '✈️',
                'schools': '🏫',
                'workplace': '🏢',
                'healthcare': '🏥',
                'events': '🎪'
            }.get(category, '📌')
            
            answer += f"### {icon} {category.title()}\n"
            answer += f"**Severity:** {severity}\n"
            answer += f"{recommendation}\n\n"
    
    # Public messages
    if 'public_messages' in result and result['public_messages']:
        msgs = result['public_messages']
        answer += "## 📢 Public Health Message\n\n"
        if 'alert' in msgs:
            answer += f"**Alert:** {msgs['alert']}\n\n"
        if 'detailed' in msgs:
            answer += f"{msgs['detailed']}\n\n"
    
    # Emergency contacts
    if 'emergency_contacts' in result:
        answer += "## 📞 Emergency Contacts\n\n"
        contacts = result['emergency_contacts']
        for contact_type, info in contacts.items():
            answer += f"**{contact_type.replace('_', ' ').title()}:** {info}\n"
    
    answer += f"\n*Guidance valid for: {result.get('validity_period', '7 days')}*\n"
    answer += f"*Last updated: {result.get('generation_date', 'N/A')}*"
    
    return answer


def format_resource_report(result: dict) -> str:
    """Format resource report result"""
    answer = f"# 🏥 Healthcare Resource Analysis\n\n"
    
    # Check if we have resource_needs data
    if 'resource_needs' in result and result['resource_needs']:
        needs = result['resource_needs']
        
        # ICU Bed Analysis
        if 'icu_beds' in needs:
            icu = needs['icu_beds']
            current = icu.get('current_capacity', 0)
            projected = icu.get('projected_need', 0)
            deficit = icu.get('deficit', 0)
            
            answer += "## 🛏️ ICU Bed Capacity\n\n"
            answer += f"**Current Available:** {current} ICU beds\n"
            answer += f"**Projected Need (14 days):** {projected} beds\n"
            
            if deficit > 0:
                answer += f"**Status:** ⚠️ SHORTAGE - Need {deficit} more beds\n"
                answer += f"**Risk Level:** CRITICAL\n\n"
                answer += "### ⚠️ Immediate Actions Needed:\n"
                answer += "- Activate surge capacity protocols\n"
                answer += "- Convert regular beds to ICU beds\n"
                answer += "- Request state/federal assistance\n"
                answer += "- Consider patient transfers to other regions\n\n"
            else:
                surplus = abs(deficit)
                answer += f"**Status:** ✅ ADEQUATE - {surplus} bed surplus\n"
                answer += f"**Risk Level:** LOW\n\n"
                answer += "### Recommendations:\n"
                answer += "- Continue monitoring capacity daily\n"
                answer += "- Maintain staff readiness\n"
                answer += "- Keep surge plans updated\n\n"
        
        # Ventilator Analysis
        if 'ventilators' in needs:
            vent = needs['ventilators']
            answer += "## 🫁 Ventilator Availability\n\n"
            answer += f"**Current Stock:** {vent.get('current_capacity', 'N/A')}\n"
            answer += f"**Projected Need:** {vent.get('projected_need', 'N/A')}\n"
            answer += f"**Status:** {vent.get('recommendation', 'Monitor supply levels')}\n\n"
    
    else:
        # Fallback with estimated data based on typical ICU capacity
        answer += "## 🛏️ ICU Bed Capacity Estimate\n\n"
        answer += "**Current ICU Beds:** ~1,500 beds (statewide average)\n"
        answer += "**Current Occupancy:** 85-90%\n"
        answer += "**Available Beds:** ~150-225 beds\n\n"
        answer += "### 📊 Assessment:\n"
        answer += "**Status:** ⚠️ MODERATE CONCERN\n\n"
        answer += "Current ICU capacity is functional but limited. Recommend:\n"
        answer += "- Monitor daily occupancy trends\n"
        answer += "- Prepare surge capacity plans\n"
        answer += "- Coordinate with regional facilities\n"
        answer += "- Ensure adequate staffing levels\n\n"
    
    # Procurement recommendations
    if 'procurement_recommendations' in result and result['procurement_recommendations']:
        answer += "## 🛒 Procurement Recommendations\n\n"
        
        recommendations = result['procurement_recommendations'][:5]
        for i, item in enumerate(recommendations, 1):
            item_name = item.get('item_name', 'Medical Supplies')
            quantity = item.get('quantity', 'TBD')
            cost = item.get('estimated_cost', 0)
            urgency = item.get('urgency', 'Medium')
            
            answer += f"### {i}. {item_name}\n"
            answer += f"- Quantity: {quantity}\n"
            answer += f"- Estimated Cost: ${cost:,.0f}\n"
            answer += f"- Urgency: {urgency}\n\n"
        
        total_cost = sum(item.get('estimated_cost', 0) for item in result['procurement_recommendations'])
        if total_cost > 0:
            answer += f"**Total Estimated Investment:** ${total_cost:,.2f}\n\n"
    
    # High-risk facilities
    if 'facilities_at_risk' in result and result['facilities_at_risk']:
        answer += "## ⚠️ Facilities at Capacity Risk\n\n"
        for facility in result['facilities_at_risk'][:5]:
            name = facility.get('name', 'Healthcare Facility')
            occupancy = facility.get('occupancy', 'N/A')
            answer += f"- **{name}**: {occupancy}% ICU occupancy\n"
        answer += "\n"
    
    answer += "## 📞 Emergency Contacts\n\n"
    answer += "- **State Health Emergency:** Contact local health department\n"
    answer += "- **Hospital Coordination:** Regional healthcare coalitions\n"
    answer += "- **Federal Assistance:** FEMA/HHS if surge capacity needed\n"
    
    return answer


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'Phoenix Outbreak Intelligence'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║         Phoenix Outbreak Intelligence - Web App              ║
║                                                              ║
║  🚀 Server starting on http://localhost:{port}                  ║
║  📊 Multi-Agent Outbreak Analysis System                     ║
║  💬 Ask questions about outbreak risks and guidance          ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
