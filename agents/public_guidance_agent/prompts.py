"""
Prompts and templates for Public Guidance Agent
Contains all prompt engineering for generating clear, actionable public health guidance
"""

# System prompt for Public Guidance Agent
SYSTEM_PROMPT = """
You are the Public Guidance Agent for Phoenix Outbreak Intelligence, specializing in translating complex epidemiological data into clear, actionable public health guidance.

Your core responsibilities:
- Convert outbreak risk analysis into practical recommendations
- Generate location-specific guidance for different audiences
- Ensure consistency with CDC, WHO, and local health authority guidelines  
- Create clear, jargon-free communication for the public
- Provide confidence-rated recommendations

Key principles:
- Evidence-based recommendations only
- Clear, actionable language (avoid medical jargon)
- Risk-proportionate responses (don't over- or under-react)
- Culturally sensitive and accessible messaging
- Always include confidence levels and data sources

Target audiences:
- General public
- Schools and educators
- Businesses and employers
- Healthcare facilities
- Community organizations
"""

# Guidance generation prompts
GUIDANCE_GENERATION_PROMPT = """
Generate comprehensive public health guidance based on this outbreak analysis:

Risk Analysis Input:
- Location: {location}
- Risk Score: {risk_score}/100
- Risk Level: {risk_level}
- Key Insights: {insights}
- Confidence: {confidence}%

Target Audience: {audience}

Generate guidance for these categories:
1. Masking recommendations
2. Travel advisory
3. School/workplace safety
4. Community events
5. Healthcare considerations

For each category, provide:
- Clear, specific recommendation
- Risk level justification
- Confidence score
- Target implementation timeframe

Use accessible language and emoji indicators for urgency levels.
"""

# Risk-level specific guidance templates
RISK_LEVEL_TEMPLATES = {
    "CRITICAL": {
        "urgency": "IMMEDIATE ACTION REQUIRED",
        "tone": "urgent but not panic-inducing",
        "messaging": "Enhanced protective measures are now in effect",
        "timeframe": "Implement immediately, review daily"
    },
    "HIGH": {
        "urgency": "ENHANCED PRECAUTIONS RECOMMENDED", 
        "tone": "serious but reassuring",
        "messaging": "Increased safety measures are strongly advised",
        "timeframe": "Implement within 24-48 hours"
    },
    "MODERATE": {
        "urgency": "STANDARD PRECAUTIONS ADVISED",
        "tone": "informative and calm",
        "messaging": "Maintain awareness and standard safety practices",
        "timeframe": "Review and adjust within one week"
    },
    "LOW": {
        "urgency": "ROUTINE MONITORING",
        "tone": "reassuring and informative", 
        "messaging": "Continue following basic health guidelines",
        "timeframe": "Standard monitoring schedule"
    }
}

# Audience-specific prompts
AUDIENCE_SPECIFIC_PROMPTS = {
    "general_public": """
    Create guidance for the general public that:
    - Uses simple, clear language (8th grade reading level)
    - Includes practical, actionable steps
    - Addresses common concerns and questions
    - Provides reassurance where appropriate
    - Includes visual indicators (emojis) for key actions
    """,
    
    "schools": """
    Create guidance for schools and educational institutions that:
    - Addresses K-12 and higher education settings
    - Covers classroom, cafeteria, and transportation considerations
    - Includes student, staff, and parent perspectives
    - Provides implementation timelines
    - Addresses learning continuity considerations
    """,
    
    "businesses": """
    Create guidance for businesses and employers that:
    - Covers office, retail, and service industry settings
    - Addresses employee safety and operational continuity
    - Includes cost-effective implementation strategies
    - Considers customer interaction protocols
    - Addresses legal compliance requirements
    """,
    
    "healthcare": """
    Create guidance for healthcare facilities that:
    - Covers hospitals, clinics, and long-term care
    - Addresses patient safety and staff protection
    - Includes surge capacity considerations
    - Covers PPE and infection control protocols
    - Addresses visitor policies and restrictions
    """
}

# Message formatting templates
MESSAGE_TEMPLATES = {
    "alert_short": {
        "template": "{emoji} {risk_level}: {location} outbreak status. {key_action}",
        "max_chars": 280,
        "platforms": ["Twitter", "SMS", "emergency alerts"]
    },
    
    "alert_medium": {
        "template": "{risk_level} outbreak activity detected in {location}.\n\nKey recommendations:\n{bullet_points}\n\nFor details: {info_source}",
        "max_chars": 1000,
        "platforms": ["Facebook", "newsletters", "website banners"]
    },
    
    "detailed_guidance": {
        "template": "Public Health Update - {location}\nRisk Level: {risk_level}\nEffective: {date}\n\n{detailed_recommendations}\n\n{disclaimer}\n{contacts}",
        "max_chars": 5000,
        "platforms": ["websites", "official announcements", "press releases"]
    }
}

# Standard disclaimers and legal language
STANDARD_DISCLAIMERS = {
    "data_based": "This guidance is based on current available data and epidemiological analysis.",
    "evolving_situation": "Recommendations may be updated as the situation evolves.",
    "individual_consultation": "For individual health decisions, consult with your healthcare provider.",
    "local_authority": "Follow additional guidance from your local health authorities.",
    "emergency": "In case of medical emergency, call 911 immediately."
}

# Confidence level messaging
CONFIDENCE_MESSAGING = {
    "high": "This recommendation is supported by strong epidemiological evidence (90%+ confidence).",
    "moderate": "This recommendation is based on available evidence with moderate confidence (70-90%).",
    "low": "This recommendation is preliminary and based on limited evidence (50-70% confidence).",
    "uncertain": "This situation requires additional monitoring due to insufficient data (<50% confidence)."
}

# Emergency escalation prompts
EMERGENCY_ESCALATION_PROMPT = """
CRITICAL OUTBREAK DETECTED - Generate emergency public health communication:

Situation:
- Location: {location}
- Risk Score: {risk_score}/100 (CRITICAL level)
- Key Drivers: {critical_factors}
- Estimated Timeline: {timeline}

Generate emergency response communication that:
1. Conveys urgency without causing panic
2. Provides immediate actionable steps
3. Directs people to official information sources
4. Includes emergency contact information
5. Uses clear, accessible language

Format for multiple channels:
- Emergency alert (160 characters)
- Social media post (280 characters)
- Press release headline and key points
- Public address talking points

Tone: Authoritative, calm, urgent but not alarming
"""

# Validation prompts for guidance quality
GUIDANCE_VALIDATION_PROMPT = """
Review this public health guidance for quality and accuracy:

Generated Guidance: {guidance_text}
Risk Level: {risk_level}
Target Audience: {audience}
Location: {location}

Validation checklist:
✓ Evidence-based recommendations
✓ Appropriate risk level response
✓ Clear, actionable language
✓ Audience-appropriate content
✓ Consistent with official guidelines
✓ Includes confidence indicators
✓ Provides next steps/resources

Flag any issues with:
- Overreaction or underreaction to risk level
- Unclear or confusing language
- Missing essential information
- Inconsistency with health authorities
- Accessibility concerns
"""

# Multi-language considerations
MULTILINGUAL_PROMPTS = {
    "spanish": "Translate and culturally adapt this guidance for Spanish-speaking communities, ensuring medical terms are accessible and cultural considerations are addressed.",
    "simplified": "Create a simplified version using basic vocabulary and shorter sentences for communities with limited English proficiency.",
    "visual": "Identify key points that should be conveyed through infographics or visual aids rather than text."
}

# Sector-specific guidance prompts
SECTOR_GUIDANCE = {
    "hospitality": "Generate guidance for restaurants, hotels, and entertainment venues focusing on customer safety and business continuity.",
    "transportation": "Create recommendations for public transit, rideshare, and travel industry operators.",
    "retail": "Develop safety protocols for stores, shopping centers, and customer-facing businesses.",
    "manufacturing": "Address workplace safety in industrial and manufacturing environments.",
    "agriculture": "Consider seasonal workers, food safety, and rural community considerations."
}