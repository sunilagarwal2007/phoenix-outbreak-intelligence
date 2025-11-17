"""
Prompts and templates for Data Intelligence Agent
Contains all prompt engineering for BigQuery analysis and risk assessment
"""

# System prompts for the Data Intelligence Agent
SYSTEM_PROMPT = """
You are the Data Intelligence Agent for Phoenix Outbreak Intelligence, a specialized AI system for public health surveillance.

Your core responsibilities:
- Analyze BigQuery public health datasets (COVID-19, influenza, CDC data)
- Detect early outbreak signals and compute risk scores
- Generate actionable intelligence for public health officials
- Validate rumors and misinformation against official data sources

Key capabilities:
- Time series analysis and trend detection
- Multi-factor risk assessment (cases, positivity, hospital capacity)
- Statistical modeling for outbreak prediction
- Data quality assessment and confidence scoring

Always provide:
- Clear risk levels (LOW/MODERATE/HIGH/CRITICAL)
- Confidence intervals for all predictions
- Data source transparency
- Actionable recommendations
"""

# Prompts for BigQuery analysis
BIGQUERY_ANALYSIS_PROMPT = """
Analyze the following public health dataset for outbreak signals:

Dataset: {dataset_name}
Location: {location}
Time Period: {start_date} to {end_date}
Metrics: {metrics}

Focus on:
1. Trend detection (increasing/decreasing/stable)
2. Anomaly identification (unusual spikes or patterns)
3. Growth rate calculation (week-over-week changes)
4. Seasonal adjustments if applicable

Provide statistical confidence for all findings.
"""

# Risk scoring prompts
RISK_SCORING_PROMPT = """
Calculate outbreak risk score (0-100) based on these components:

Case Trends: {case_data}
- Daily counts: {daily_counts}
- 7-day average: {seven_day_avg}
- Growth rate: {growth_rate}

Test Positivity: {positivity_data}
- Current rate: {current_rate}
- Trend: {trend}
- CDC threshold comparison: {cdc_comparison}

Hospital Capacity: {hospital_data}
- ICU occupancy: {icu_occupancy}
- Bed availability: {bed_availability}
- Strain indicator: {strain_level}

Apply weighting:
- Case trends: 30%
- Positivity: 30% 
- Hospital strain: 40%

Output format:
- Overall Risk Score: [0-100]
- Risk Level: [LOW/MODERATE/HIGH/CRITICAL]
- Confidence: [percentage]
- Key drivers: [top 3 factors]
"""

# Rumor validation prompts
RUMOR_VALIDATION_PROMPT = """
Validate the following outbreak-related claim against official data:

Claim: "{rumor_text}"
Location: {location}
Date: {analysis_date}

Available official data sources:
- CDC datasets: {cdc_data}
- State health department: {state_data}
- Hospital systems: {hospital_data}
- Academic studies: {academic_data}

Analysis framework:
1. Fact extraction from claim
2. Data source cross-reference
3. Statistical verification
4. Confidence assessment

Verdict options:
- CONFIRMED: Supported by official data
- FALSE: Contradicted by official data
- PARTIALLY TRUE: Some elements confirmed
- INSUFFICIENT DATA: Cannot verify with available sources
- INVESTIGATING: Requires additional data collection

Provide evidence summary and confidence percentage.
"""

# Insight generation prompts
INSIGHT_GENERATION_PROMPT = """
Generate actionable public health insights from this analysis:

Risk Assessment Results:
- Location: {location}
- Risk Score: {risk_score}
- Risk Level: {risk_level}
- Key Trends: {trends}

Target Audience: Public health officials, emergency planners
Tone: Professional, urgent when appropriate, evidence-based

Generate insights for:
1. Immediate actions (next 24-48 hours)
2. Short-term monitoring (next 1-2 weeks)
3. Resource planning considerations
4. Public communication recommendations

Format as bullet points with emoji indicators for urgency level.
"""

# Data quality assessment prompts
DATA_QUALITY_PROMPT = """
Assess the quality and reliability of this health surveillance data:

Dataset: {dataset_info}
Coverage: {temporal_coverage}
Completeness: {data_completeness}
Timeliness: {last_updated}
Source: {data_source}

Quality factors to evaluate:
- Temporal consistency (regular reporting)
- Geographic coverage (complete vs. partial)
- Reporting delays (real-time vs. lag)
- Missing data patterns
- Source reliability

Provide quality score (0-100) and adjust analysis confidence accordingly.
Highlight any limitations that should be communicated to decision-makers.
"""

# Prompt templates for different query types
QUERY_TEMPLATES = {
    "daily_cases": """
    SELECT 
        date,
        location,
        new_cases,
        cumulative_cases,
        population
    FROM `{project}.{dataset}.covid19_cases`
    WHERE location LIKE '%{location}%'
    AND date BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY date DESC
    """,
    
    "positivity_rates": """
    SELECT 
        date,
        location,
        tests_performed,
        positive_tests,
        SAFE_DIVIDE(positive_tests, tests_performed) as positivity_rate
    FROM `{project}.{dataset}.covid19_testing`
    WHERE location LIKE '%{location}%'
    AND date BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY date DESC
    """,
    
    "hospital_capacity": """
    SELECT 
        date,
        location,
        icu_beds_total,
        icu_beds_occupied,
        SAFE_DIVIDE(icu_beds_occupied, icu_beds_total) as icu_occupancy
    FROM `{project}.{dataset}.hospital_capacity`
    WHERE location LIKE '%{location}%'
    AND date BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY date DESC
    """,
}

# Response formatting templates
RESPONSE_TEMPLATES = {
    "risk_assessment": {
        "high_risk": "🚨 **HIGH RISK DETECTED** 🚨\nImmediate intervention recommended for {location}. Risk score: {score}/100.",
        "moderate_risk": "⚠️ **MODERATE RISK** ⚠️\nEnhanced monitoring advised for {location}. Risk score: {score}/100.",
        "low_risk": "✅ **LOW RISK** ✅\nStandard monitoring protocols sufficient for {location}. Risk score: {score}/100."
    },
    
    "trend_alert": {
        "accelerating": "📈 **ACCELERATING TREND**: Cases increasing at {rate}% week-over-week in {location}",
        "stable": "📊 **STABLE TREND**: Case counts relatively steady in {location}",
        "declining": "📉 **DECLINING TREND**: Cases decreasing at {rate}% week-over-week in {location}"
    }
}

# Validation rules for data inputs
VALIDATION_RULES = {
    "location_formats": [
        r"^[A-Za-z\s]+,\s*[A-Z]{2}$",  # City, STATE
        r"^[A-Za-z\s]+\s+County$",      # County Name County
        r"^[A-Za-z\s]+$"                # State or City name
    ],
    
    "date_formats": [
        r"^\d{4}-\d{2}-\d{2}$",         # YYYY-MM-DD
        r"^\d{2}/\d{2}/\d{4}$",         # MM/DD/YYYY
    ],
    
    "risk_score_range": (0, 100),
    "confidence_range": (0, 100),
    "max_analysis_days": 365
}