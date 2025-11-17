"""
Public Guidance Agent for Phoenix Outbreak Intelligence
Converts outbreak intelligence into clear, actionable public health guidance
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import sys
import os
from pathlib import Path

# Add parent directory to path to import gemini_helper
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from gemini_helper import GeminiAIHelper, generate_public_guidance_with_gemini

# Import MCP Tools
try:
    from mcp.web_reader.web_reader_mcp_server import WebReaderMCPServer
    from mcp.google_maps.maps_mcp_agent import GoogleMapsMCPAgent
    MCP_AVAILABLE = True
except ImportError as e:
    logging.warning(f"MCP tools not available: {e}")
    MCP_AVAILABLE = False

# System prompts for guidance generation
PUBLIC_GUIDANCE_SYSTEM_PROMPT = """
You are the Public Health Guidance Agent for the Phoenix Outbreak Intelligence System.

Your responsibilities:
- Provide VERIFIED, accurate, up-to-date health guidance.
- Use ONLY data provided by the Data Intel Agent, WHO, CDC, valid sources.
- Use MCP tools (Google Maps, Web Reader) only when clearly helpful.
- NEVER fabricate statistics.
- ALWAYS respond in a calm, helpful tone.

Your tasks:
1. Translate outbreak data into clear public-facing guidance.
2. Provide location-specific recommendations if location is given.
3. Warn users about misinformation when needed.
4. Provide step-by-step instructions for self-care, risk reduction, and resource navigation.
5. When needed, recommend local hospitals, clinics, or emergency rooms (using Google Maps MCP).

Output Requirements:
- Simple language
- Actionable steps
- No medical diagnosis
- Always encourage consulting local authorities for critical decisions
"""

PUBLIC_GUIDANCE_RUMOR_PROMPT = """
You received a message that appears to be misinformation or a rumor.

Evaluate the claim using:
- WHO verified guidance
- CDC verified guidance
- Data Intel outputs
- MCP web-reader content (if provided)

Return:
- A clear verdict: TRUE, FALSE, or PARTIALLY TRUE
- A short explanation why (citing verified reasoning)
- Provide corrected information
- Provide safe next steps
"""

@dataclass
class GuidanceRecommendation:
    """Structure for individual guidance recommendations"""
    category: str  # "masking", "travel", "schools", "workplace", etc.
    recommendation: str
    severity_level: str  # "LOW", "MODERATE", "HIGH", "CRITICAL"
    confidence: float
    target_audience: str
    effective_date: str
    source_evidence: List[str]

class PublicGuidanceAgent:
    """
    Agent responsible for:
    - Converting risk analysis into public health guidance
    - Generating location-specific recommendations
    - Creating clear, actionable advice for different audiences
    - Maintaining consistency with CDC/WHO guidelines
    """
    
    def __init__(self, project_id: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.guidance_templates = self._load_guidance_templates()
        
        # Initialize Gemini AI for guidance generation
        try:
            if project_id:
                self.gemini = GeminiAIHelper(project_id=project_id)
                self.logger.info("Gemini AI initialized successfully")
            else:
                self.gemini = None
                self.logger.info("Running without Gemini AI (project_id not provided)")
        except Exception as e:
            self.logger.warning(f"Could not initialize Gemini AI: {e}")
            self.gemini = None
        
        # Initialize MCP Tools (Model Context Protocol)
        self.mcp_web_reader = None
        self.mcp_maps = None
        
        if MCP_AVAILABLE:
            try:
                # Google Maps MCP for finding nearby healthcare facilities
                maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
                if maps_api_key:
                    self.mcp_maps = GoogleMapsMCPAgent(api_key=maps_api_key)
                    self.logger.info("✓ MCP: Google Maps Agent initialized")
                else:
                    self.logger.warning("⚠ MCP: GOOGLE_MAPS_API_KEY not set")
                
                # Web Reader MCP will be initialized per-request (async context manager)
                self.logger.info("✓ MCP: Web Reader available for rumor validation")
                
            except Exception as e:
                self.logger.warning(f"⚠ MCP initialization failed: {e}")
        else:
            self.logger.warning("⚠ MCP tools not available - install dependencies")
        
    async def generate_public_guidance(self, risk_analysis: Dict, location: str, 
                                     target_audience: str = "general_public") -> Dict:
        """
        Main function to generate comprehensive public health guidance
        
        Args:
            risk_analysis: Output from DataIntelligenceAgent
            location: Geographic location for guidance
            target_audience: "general_public", "schools", "businesses", "healthcare"
            
        Returns:
            Dict containing structured guidance recommendations
        """
        try:
            risk_score = risk_analysis.get("risk_score", 0)
            risk_level = risk_analysis.get("risk_level", "LOW")
            insights = risk_analysis.get("insights", [])
            
            # Generate category-specific guidance
            guidance_categories = await self._generate_guidance_by_category(
                risk_score, risk_level, location, target_audience
            )
            
            # Create summary recommendations
            key_recommendations = self._create_key_recommendations(
                guidance_categories, risk_level
            )
            
            # Generate communication messages
            public_messages = await self._generate_public_messages(
                guidance_categories, risk_level, location
            )
            
            return {
                "location": location,
                "target_audience": target_audience,
                "generation_date": datetime.now().isoformat(),
                "risk_context": {
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "key_insights": insights
                },
                "guidance_categories": guidance_categories,
                "key_recommendations": key_recommendations,
                "public_messages": public_messages,
                "last_updated": datetime.now().isoformat(),
                "validity_period": "7 days",
                "emergency_contacts": self._get_emergency_contacts(location)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating public guidance: {str(e)}")
            raise
    
    async def _generate_guidance_by_category(self, risk_score: float, risk_level: str,
                                           location: str, audience: str) -> Dict:
        """Generate specific guidance for each category"""
        categories = {}
        
        # Masking guidance
        categories["masking"] = self._generate_masking_guidance(
            risk_score, risk_level, audience
        )
        
        # Travel guidance
        categories["travel"] = self._generate_travel_guidance(
            risk_score, risk_level, location
        )
        
        # School guidance
        categories["schools"] = self._generate_school_guidance(
            risk_score, risk_level
        )
        
        # Workplace guidance
        categories["workplace"] = self._generate_workplace_guidance(
            risk_score, risk_level
        )
        
        # Healthcare guidance
        categories["healthcare"] = self._generate_healthcare_guidance(
            risk_score, risk_level
        )
        
        # Community events guidance
        categories["events"] = self._generate_events_guidance(
            risk_score, risk_level
        )
        
        return categories
    
    def _generate_masking_guidance(self, risk_score: float, risk_level: str, 
                                  audience: str) -> GuidanceRecommendation:
        """Generate masking recommendations based on risk level"""
        if risk_level == "CRITICAL":
            recommendation = "Universal masking required in ALL indoor settings. N95 or KN95 masks strongly recommended."
            severity = "CRITICAL"
        elif risk_level == "HIGH":
            recommendation = "Masks required in healthcare, public transit, and crowded indoor settings. Strongly recommended for all indoor activities."
            severity = "HIGH"
        elif risk_level == "MODERATE":
            recommendation = "Masks recommended in healthcare settings and crowded indoor spaces. Consider masking if high-risk."
            severity = "MODERATE"
        else:
            recommendation = "Masks optional for general public. Follow facility-specific requirements."
            severity = "LOW"
        
        return GuidanceRecommendation(
            category="masking",
            recommendation=recommendation,
            severity_level=severity,
            confidence=0.95,
            target_audience=audience,
            effective_date=datetime.now().isoformat(),
            source_evidence=["CDC guidelines", "Local outbreak data"]
        )
    
    def _generate_travel_guidance(self, risk_score: float, risk_level: str,
                                 location: str) -> GuidanceRecommendation:
        """Generate travel recommendations"""
        if risk_level == "CRITICAL":
            recommendation = f"Avoid non-essential travel to/from {location}. If travel necessary, take enhanced precautions."
        elif risk_level == "HIGH":
            recommendation = f"Consider postponing non-essential travel to/from {location}. Enhanced testing and precautions recommended."
        elif risk_level == "MODERATE":
            recommendation = f"Monitor conditions before traveling to/from {location}. Standard precautions recommended."
        else:
            recommendation = "No travel restrictions. Follow standard health precautions."
        
        return GuidanceRecommendation(
            category="travel",
            recommendation=recommendation,
            severity_level=risk_level,
            confidence=0.90,
            target_audience="general_public",
            effective_date=datetime.now().isoformat(),
            source_evidence=["Travel pattern analysis", "Regional outbreak data"]
        )
    
    def _generate_school_guidance(self, risk_score: float, 
                                 risk_level: str) -> GuidanceRecommendation:
        """Generate school-specific recommendations"""
        if risk_level == "CRITICAL":
            recommendation = "Consider temporary remote learning. If in-person, require masks, enhanced ventilation, and daily health screenings."
        elif risk_level == "HIGH":
            recommendation = "Enhanced safety measures: universal masking, improved ventilation, health screenings, and social distancing where possible."
        elif risk_level == "MODERATE":
            recommendation = "Standard safety measures: health screenings, improved ventilation, and masks in common areas."
        else:
            recommendation = "Maintain standard health protocols. Monitor for symptoms and stay home when sick."
        
        return GuidanceRecommendation(
            category="schools",
            recommendation=recommendation,
            severity_level=risk_level,
            confidence=0.88,
            target_audience="schools",
            effective_date=datetime.now().isoformat(),
            source_evidence=["School transmission data", "CDC school guidelines"]
        )
    
    def _generate_workplace_guidance(self, risk_score: float,
                                    risk_level: str) -> GuidanceRecommendation:
        """Generate workplace recommendations"""
        if risk_level == "CRITICAL":
            recommendation = "Implement remote work where possible. Enhanced ventilation, universal masking, and health screenings for essential workers."
        elif risk_level == "HIGH":
            recommendation = "Consider hybrid work arrangements. Enhanced cleaning, masking in common areas, and improved ventilation."
        elif risk_level == "MODERATE":
            recommendation = "Flexible work options. Standard cleaning protocols and encourage sick workers to stay home."
        else:
            recommendation = "Maintain standard workplace health practices. Encourage vaccination and good hygiene."
        
        return GuidanceRecommendation(
            category="workplace",
            recommendation=recommendation,
            severity_level=risk_level,
            confidence=0.92,
            target_audience="businesses",
            effective_date=datetime.now().isoformat(),
            source_evidence=["Workplace transmission studies", "OSHA guidelines"]
        )
    
    def _generate_healthcare_guidance(self, risk_score: float,
                                     risk_level: str) -> GuidanceRecommendation:
        """Generate healthcare facility recommendations"""
        if risk_level in ["CRITICAL", "HIGH"]:
            recommendation = "Activate surge capacity protocols. Universal masking, enhanced PPE, and visitor restrictions."
        elif risk_level == "MODERATE":
            recommendation = "Review capacity planning. Standard infection control with enhanced monitoring."
        else:
            recommendation = "Maintain standard infection control practices. Monitor for changes in patient volumes."
        
        return GuidanceRecommendation(
            category="healthcare",
            recommendation=recommendation,
            severity_level=risk_level,
            confidence=0.97,
            target_audience="healthcare",
            effective_date=datetime.now().isoformat(),
            source_evidence=["Hospital capacity data", "Infection control guidelines"]
        )
    
    def _generate_events_guidance(self, risk_score: float,
                                 risk_level: str) -> GuidanceRecommendation:
        """Generate community events recommendations"""
        if risk_level == "CRITICAL":
            recommendation = "Cancel or postpone large indoor events. Outdoor events with enhanced safety measures only."
        elif risk_level == "HIGH":
            recommendation = "Limit large indoor gatherings. Require safety measures for events (masking, ventilation, health checks)."
        elif risk_level == "MODERATE":
            recommendation = "Standard event safety measures. Consider venue capacity and ventilation quality."
        else:
            recommendation = "No event restrictions. Follow venue-specific health guidelines."
        
        return GuidanceRecommendation(
            category="events",
            recommendation=recommendation,
            severity_level=risk_level,
            confidence=0.85,
            target_audience="event_organizers",
            effective_date=datetime.now().isoformat(),
            source_evidence=["Event transmission data", "Venue guidelines"]
        )
    
    def _create_key_recommendations(self, categories: Dict, 
                                   risk_level: str) -> List[str]:
        """Create summary of top 5 key recommendations"""
        recommendations = []
        
        # Priority order based on risk level
        if risk_level in ["CRITICAL", "HIGH"]:
            recommendations = [
                f"😷 {categories['masking'].recommendation}",
                f"🏢 {categories['workplace'].recommendation}",
                f"🏫 {categories['schools'].recommendation}",
                f"✈️ {categories['travel'].recommendation}",
                f"🎪 {categories['events'].recommendation}"
            ]
        else:
            recommendations = [
                f"😷 {categories['masking'].recommendation}",
                f"✈️ {categories['travel'].recommendation}",
                f"🏫 {categories['schools'].recommendation}",
                f"🏢 {categories['workplace'].recommendation}",
                f"🎪 {categories['events'].recommendation}"
            ]
        
        return recommendations[:5]  # Top 5 recommendations
    
    async def _generate_public_messages(self, categories: Dict, risk_level: str,
                                       location: str) -> Dict:
        """Generate public communication messages"""
        messages = {}
        
        # Use Gemini AI for message generation if available
        if self.gemini:
            try:
                # Generate alert message with Gemini using system prompt
                alert_prompt = f"""{PUBLIC_GUIDANCE_SYSTEM_PROMPT}

TASK: Create a brief public health alert for {location} with risk level {risk_level}.

Risk Context:
- Risk Level: {risk_level}
- Location: {location}
- Available Guidance Categories: {list(categories.keys())}

Requirements:
1. Appropriate emoji based on urgency (🚨 CRITICAL, ⚠️ HIGH, 🔶 MODERATE, ✅ LOW)
2. Clear risk level indicator
3. One-sentence action statement
4. Keep under 150 characters
5. Calm, helpful tone - NOT alarmist

Format: [Emoji] [RISK LEVEL]: [Brief actionable message]

Remember: Use ONLY verified information, be helpful and reassuring."""
                
                messages["alert"] = self.gemini.generate_text(alert_prompt, temperature=0.3, max_output_tokens=100).strip()
                
                # Generate detailed message with system prompt
                detailed_prompt = f"""{PUBLIC_GUIDANCE_SYSTEM_PROMPT}

TASK: Create a detailed public health guidance message for {location}.

Risk Context:
- Risk Level: {risk_level}
- Location: {location}

Guidance Available:
- Masking: {categories.get('masking', 'N/A')}
- Travel: {categories.get('travel', 'N/A')}
- Schools: {categories.get('schools', 'N/A')}
- Workplace: {categories.get('workplace', 'N/A')}
- Healthcare: {categories.get('healthcare', 'N/A')}
- Events: {categories.get('events', 'N/A')}

Structure your response:
1. Clear header acknowledging the situation
2. Current situation summary (2-3 sentences) - factual, not alarming
3. 3-5 key actionable recommendations (numbered list)
4. Specific guidance for different groups (general public, vulnerable populations)
5. When to seek medical care (symptoms to watch for)
6. Encouragement to follow local health authorities
7. Reassuring closing statement

Tone: Professional, calm, helpful, empowering
Length: 300-500 words
No medical diagnosis - always defer to healthcare providers for personal health decisions."""
                
                messages["detailed"] = self.gemini.generate_text(detailed_prompt, temperature=0.4, max_output_tokens=3072).strip()
                
                # Generate social media message with system prompt
                social_prompt = f"""{PUBLIC_GUIDANCE_SYSTEM_PROMPT}

TASK: Create a social media post about {risk_level} outbreak activity in {location}.

Requirements:
- Include relevant emoji for visibility
- Under 280 characters (Twitter-friendly)
- Include #PublicHealth hashtag
- Clear but not alarmist - we want to inform, not panic
- Encourage following local health guidance
- Actionable advice in simple language

Example format:
[Emoji] [Brief situation] in {location}. [Key action]. Follow local health guidance. #PublicHealth #[Location]

Remember: Verified information only, helpful tone, no fear-mongering."""
                
                messages["social_media"] = self.gemini.generate_text(social_prompt, temperature=0.3, max_output_tokens=100).strip()
                
                return messages
                
            except Exception as e:
                self.logger.warning(f"Gemini message generation failed: {e}, falling back to templates")
        
        # Fallback to template-based messages
        # Short summary (for alerts/notifications)
        if risk_level == "CRITICAL":
            messages["alert"] = f"🚨 CRITICAL: High outbreak activity in {location}. Enhanced safety measures in effect."
        elif risk_level == "HIGH":
            messages["alert"] = f"⚠️ HIGH ALERT: Increased outbreak activity in {location}. Take enhanced precautions."
        elif risk_level == "MODERATE":
            messages["alert"] = f"🔶 MODERATE: Elevated outbreak activity in {location}. Standard precautions advised."
        else:
            messages["alert"] = f"✅ LOW RISK: Current outbreak activity in {location} remains low."
        
        # Detailed public message
        messages["detailed"] = self._create_detailed_public_message(
            categories, risk_level, location
        )
        
        # Social media message
        messages["social_media"] = self._create_social_media_message(
            risk_level, location
        )
        
        return messages
    
    def _create_detailed_public_message(self, categories: Dict, 
                                       risk_level: str, location: str) -> str:
        """Create detailed public health message"""
        header = f"Public Health Update for {location}"
        
        if risk_level == "CRITICAL":
            urgency = "immediate action is required"
        elif risk_level == "HIGH":
            urgency = "enhanced precautions are strongly recommended"
        elif risk_level == "MODERATE":
            urgency = "standard precautions should be maintained"
        else:
            urgency = "continue following basic health guidelines"
        
        message = f"""
{header}
Risk Level: {risk_level}

Based on current outbreak data analysis, {urgency} in {location}.

KEY RECOMMENDATIONS:
• Masking: {categories['masking'].recommendation}
• Travel: {categories['travel'].recommendation}
• Schools: {categories['schools'].recommendation}
• Workplaces: {categories['workplace'].recommendation}

For the latest information, consult your local health department.
Stay informed, stay safe.
        """
        
        return message.strip()
    
    def _create_social_media_message(self, risk_level: str, location: str) -> str:
        """Create concise social media appropriate message"""
        emoji_map = {
            "CRITICAL": "🚨",
            "HIGH": "⚠️",
            "MODERATE": "🔶",
            "LOW": "✅"
        }
        
        emoji = emoji_map.get(risk_level, "ℹ️")
        
        return f"{emoji} {risk_level} outbreak activity in {location}. Follow local health guidance. #PublicHealth #OutbreakResponse"
    
    def _get_emergency_contacts(self, location: str) -> Dict:
        """Provide relevant emergency contact information"""
        return {
            "local_health_department": f"Contact your {location} health department",
            "cdc_hotline": "1-800-CDC-INFO (1-800-232-4636)",
            "emergency": "911",
            "poison_control": "1-800-222-1222",
            "mental_health_crisis": "988"
        }
    
    def _load_guidance_templates(self) -> Dict:
        """Load pre-defined guidance templates"""
        # This would load from external files or database
        return {
            "standard_disclaimer": "This guidance is based on current available data and may be updated as the situation evolves.",
            "consultation_advice": "Consult with healthcare providers for individual health decisions.",
            "source_attribution": "Based on analysis by Phoenix Outbreak Intelligence System"
        }
    
    # ========== MCP TOOL INTEGRATION ==========
    
    async def validate_rumor_with_mcp(self, claim: str, location: str = None) -> Dict:
        """
        Use MCP Web Reader to validate health claims against official sources
        
        Args:
            claim: The health claim/rumor to validate
            location: Geographic context for validation
            
        Returns:
            Validation result with verdict and evidence
        """
        if not MCP_AVAILABLE:
            self.logger.warning("MCP Web Reader not available, using fallback")
            return {
                "verdict": "UNVERIFIED",
                "confidence": 0.0,
                "explanation": "MCP Web Reader not available for validation",
                "sources": [],
                "recommendation": "Check official sources like CDC.gov or WHO.int"
            }
        
        try:
            self.logger.info(f"🔍 MCP: Validating claim with Web Reader: {claim[:100]}...")
            
            async with WebReaderMCPServer() as web_reader:
                validation_result = await web_reader.validate_health_claims(
                    claims=[claim],
                    location=location
                )
                
                if validation_result and "results" in validation_result:
                    claim_result = validation_result["results"].get(claim, {})
                    
                    self.logger.info(f"✓ MCP: Validation complete - Verdict: {claim_result.get('verdict', 'UNKNOWN')}")
                    
                    return {
                        "verdict": claim_result.get("verdict", "UNVERIFIED"),
                        "confidence": claim_result.get("confidence", 0.0),
                        "explanation": claim_result.get("explanation", "No explanation available"),
                        "sources": claim_result.get("sources", []),
                        "recommendation": claim_result.get("recommendation", "Consult official health sources")
                    }
            
        except Exception as e:
            self.logger.error(f"❌ MCP Web Reader error: {e}")
            return {
                "verdict": "ERROR",
                "confidence": 0.0,
                "explanation": f"Validation failed: {str(e)}",
                "sources": [],
                "recommendation": "Unable to validate at this time. Check CDC.gov or WHO.int"
            }
    
    async def find_nearby_facilities_with_mcp(self, location: str, facility_type: str = "hospital", radius: int = 10000) -> List[Dict]:
        """
        Use MCP Google Maps to find nearby healthcare facilities
        
        Args:
            location: Location to search near (e.g., "Los Angeles, CA")
            facility_type: Type of facility ("hospital", "clinic", "pharmacy")
            radius: Search radius in meters (default 10km)
            
        Returns:
            List of nearby facilities with details
        """
        if not self.mcp_maps:
            self.logger.warning("MCP Google Maps not available, using fallback")
            return [{
                "name": f"Contact {location} Health Department",
                "address": "Use Google Maps or local directory",
                "distance": "N/A",
                "phone": "Call 211 for local health resources"
            }]
        
        try:
            self.logger.info(f"🗺️ MCP: Finding {facility_type}s near {location} (radius: {radius}m)...")
            
            facilities = await self.mcp_maps.find_nearby_facilities(
                location=location,
                facility_type=facility_type,
                radius=radius
            )
            
            self.logger.info(f"✓ MCP: Found {len(facilities)} facilities")
            
            return facilities
            
        except Exception as e:
            self.logger.error(f"❌ MCP Google Maps error: {e}")
            return [{
                "name": f"Search Error - Try Google Maps",
                "address": f"Search for '{facility_type}s near {location}'",
                "distance": "N/A",
                "phone": "N/A",
                "error": str(e)
            }]