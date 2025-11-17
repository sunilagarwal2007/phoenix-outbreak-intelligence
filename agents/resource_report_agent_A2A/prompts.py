"""
Prompts for Resource Report Agent (A2A)
Contains prompts for resource planning, cost analysis, and report generation
"""

# System prompt for Resource Report Agent
SYSTEM_PROMPT = """
You are the Resource Report Agent (A2A) for Phoenix Outbreak Intelligence, deployed on Cloud Run as a specialized microservice for healthcare resource planning and allocation.

Your core responsibilities:
- Analyze healthcare facility capacity and project resource needs
- Generate comprehensive resource allocation reports
- Calculate procurement timelines and costs
- Optimize resource distribution and logistics
- Create executive-ready PDF reports with visualizations
- Interface with supply chain and emergency management systems

Key capabilities:
- ICU/hospital bed capacity forecasting
- PPE consumption modeling
- Testing capacity planning
- Staff allocation analysis  
- Cost-benefit analysis
- Geographic optimization using Maps API
- PDF report generation with charts and recommendations

Output requirements:
- Actionable procurement recommendations
- Detailed cost analysis with funding sources
- Implementation timelines
- Risk-adjusted projections
- Executive summaries for decision makers
"""

# Resource projection prompts
RESOURCE_PROJECTION_PROMPT = """
Calculate healthcare resource projections based on outbreak analysis:

Input Parameters:
- Location: {location}
- Risk Score: {risk_score}/100
- Growth Rate: {growth_rate}%
- Forecast Period: {forecast_days} days
- Current Utilization: {current_utilization}%

Resource Categories to Analyze:
1. ICU Beds
2. Medical/Surgical Beds
3. Ventilators
4. Testing Capacity
5. PPE Requirements
6. Healthcare Staff

For each resource:
- Calculate current capacity
- Project demand based on risk level and growth rate
- Identify shortages and surpluses
- Assign priority levels (CRITICAL/HIGH/MODERATE/LOW)
- Estimate procurement timeline
- Calculate costs

Consider factors:
- Seasonal patterns
- Regional capacity sharing
- Emergency stockpile availability
- Supply chain constraints
"""

# Facility assessment prompt
FACILITY_ASSESSMENT_PROMPT = """
Assess healthcare facility capacity and resource needs:

Facility Information:
- Name: {facility_name}
- Type: {facility_type}
- Location: {coordinates}
- Current Capacity: {current_capacity}
- Utilization Rate: {utilization_rate}%

Assessment Framework:
1. Capacity Analysis
   - Current bed utilization
   - ICU availability
   - Equipment status
   - Staff levels

2. Surge Capacity
   - Maximum expandable capacity
   - Time to activate surge
   - Resource requirements for surge
   - Staffing requirements

3. Resource Gaps
   - Immediate shortages
   - Projected shortages
   - Critical equipment needs
   - Staff deficiencies

4. Risk Factors
   - Age of equipment
   - Staff burnout indicators
   - Supply chain vulnerabilities
   - Infrastructure limitations

Generate facility-specific recommendations with priority levels and implementation timelines.
"""

# Cost analysis prompts
COST_ANALYSIS_PROMPT = """
Perform comprehensive cost analysis for resource procurement:

Resource Requirements: {resource_requirements}
Procurement Timeline: {timeline}
Market Conditions: {market_conditions}

Cost Categories:
1. Capital Expenditures
   - Equipment purchases
   - Facility modifications
   - Technology implementations

2. Operational Costs
   - PPE consumption (daily/weekly/monthly)
   - Additional staffing
   - Maintenance and supplies

3. Emergency Procurement
   - Rush delivery premiums
   - Alternative supplier costs
   - Temporary equipment rentals

4. Hidden Costs
   - Training requirements
   - Installation and setup
   - Regulatory compliance
   - Storage and logistics

Provide:
- Detailed cost breakdown
- Funding source recommendations
- Cost-benefit analysis
- Risk-adjusted estimates
- ROI calculations for long-term investments
"""

# Procurement recommendations prompt
PROCUREMENT_RECOMMENDATION_PROMPT = """
Generate actionable procurement recommendations:

Resource Gap Analysis: {gap_analysis}
Budget Constraints: {budget}
Timeline Requirements: {timeline}
Strategic Priorities: {priorities}

Recommendation Framework:
1. Immediate Actions (0-3 days)
   - Emergency procurement
   - Existing stockpile activation
   - Mutual aid agreements

2. Short-term Solutions (3-14 days)
   - Standard procurement processes
   - Vendor negotiations
   - Regional coordination

3. Long-term Planning (14+ days)
   - Strategic stockpiling
   - Infrastructure improvements
   - Capacity building

For each recommendation provide:
- Specific quantities and specifications
- Vendor/supplier options
- Cost estimates
- Implementation timeline
- Risk mitigation strategies
- Alternative approaches
"""

# PDF report generation prompt
PDF_REPORT_PROMPT = """
Generate executive-ready PDF report structure:

Report Sections:
1. Executive Summary
   - Key findings (2-3 bullet points)
   - Critical actions required
   - Funding requirements
   - Timeline overview

2. Situation Analysis
   - Current outbreak status
   - Risk assessment summary
   - Facility capacity overview

3. Resource Projections
   - Demand forecasting
   - Capacity gaps identification
   - Priority resource needs

4. Procurement Plan
   - Immediate actions required
   - Procurement timeline
   - Vendor recommendations
   - Cost breakdown

5. Implementation Strategy
   - Phase 1: Emergency response
   - Phase 2: Capacity expansion
   - Phase 3: Strategic positioning

6. Appendices
   - Facility assessments
   - Cost calculations
   - Contact information
   - Alternative scenarios

Visual Elements:
- Capacity utilization charts
- Cost breakdown pie charts
- Timeline Gantt charts
- Geographic distribution maps
- Risk level indicators
"""

# Logistics optimization prompts
LOGISTICS_OPTIMIZATION_PROMPT = """
Optimize resource distribution and logistics:

Distribution Requirements:
- Facilities: {facilities_list}
- Resource Types: {resource_types}
- Quantities: {quantities}
- Urgency Levels: {urgency_levels}

Optimization Factors:
1. Geographic Constraints
   - Facility locations
   - Transportation networks
   - Delivery accessibility

2. Timing Requirements
   - Critical delivery windows
   - Facility operating schedules
   - Peak traffic considerations

3. Resource Characteristics
   - Storage requirements
   - Handling specifications
   - Shelf life considerations
   - Temperature sensitivity

4. Cost Considerations
   - Delivery costs
   - Fuel expenses
   - Driver availability
   - Route efficiency

Generate:
- Optimal delivery routes
- Delivery schedule recommendations
- Resource allocation priorities
- Contingency plans for delays
- Communication protocols
"""

# Templates for different report types
REPORT_TEMPLATES = {
    "emergency_response": {
        "title": "Emergency Resource Allocation Report",
        "urgency": "IMMEDIATE ACTION REQUIRED",
        "timeline": "0-72 hours",
        "focus": "Critical shortages and immediate needs"
    },
    
    "capacity_planning": {
        "title": "Healthcare Capacity Planning Report", 
        "urgency": "STRATEGIC PLANNING",
        "timeline": "2-4 weeks",
        "focus": "Long-term capacity and infrastructure needs"
    },
    
    "procurement_analysis": {
        "title": "Resource Procurement Analysis",
        "urgency": "PROCUREMENT ACTION",
        "timeline": "1-2 weeks", 
        "focus": "Detailed procurement recommendations and costs"
    }
}

# Quality control prompts
QUALITY_CONTROL_PROMPT = """
Review resource report for accuracy and completeness:

Report Elements to Validate:
1. Data Accuracy
   - Capacity calculations
   - Cost estimates
   - Timeline projections
   - Growth rate applications

2. Recommendation Quality
   - Feasibility assessment
   - Priority alignment
   - Implementation clarity
   - Risk consideration

3. Report Completeness
   - All required sections included
   - Executive summary clarity
   - Supporting data provided
   - Contact information current

4. Professional Standards
   - Clear, actionable language
   - Appropriate urgency level
   - Consistent formatting
   - Error-free content

Flag any issues with:
- Unrealistic projections
- Missing critical information
- Inconsistent recommendations
- Unclear implementation guidance
"""