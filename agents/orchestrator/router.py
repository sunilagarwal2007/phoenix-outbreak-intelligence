"""
Router for Phoenix Outbreak Intelligence
Handles intent classification and request routing to appropriate agents
"""

import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
import re

class UserIntent(Enum):
    """User intent classifications"""
    OUTBREAK_STATUS = "outbreak_status"
    RISK_ASSESSMENT = "risk_assessment"
    PUBLIC_GUIDANCE = "public_guidance"
    RESOURCE_PLANNING = "resource_planning"
    SCHOOL_GUIDANCE = "school_guidance"
    TRAVEL_GUIDANCE = "travel_guidance"
    HOSPITAL_CAPACITY = "hospital_capacity"
    RUMOR_VALIDATION = "rumor_validation"
    GENERAL_INFORMATION = "general_information"
    EMERGENCY_ALERT = "emergency_alert"

class PhoenixRouter:
    """
    Intelligent router that classifies user intents and routes requests
    to the appropriate specialized agents
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.intent_patterns = self._load_intent_patterns()
        
    async def route_request(self, user_input: str, location: str = None) -> Dict:
        """
        Route user request to appropriate agent workflow
        
        Args:
            user_input: User's natural language input
            location: Optional location context
            
        Returns:
            Dict containing routing decision and extracted parameters
        """
        try:
            # Classify user intent
            intent, confidence = await self._classify_intent(user_input)
            
            # Extract entities and parameters
            entities = await self._extract_entities(user_input, location)
            
            # Determine routing strategy
            routing_strategy = await self._determine_routing_strategy(
                intent, entities, confidence
            )
            
            return {
                "intent": intent.value,
                "confidence": confidence,
                "entities": entities,
                "routing_strategy": routing_strategy,
                "user_input": user_input,
                "processing_timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"Error in routing request: {str(e)}")
            return self._create_fallback_routing(user_input, location)
    
    async def _classify_intent(self, user_input: str) -> Tuple[UserIntent, float]:
        """
        Classify user intent using pattern matching and keywords
        
        Returns:
            Tuple of (intent, confidence_score)
        """
        user_input_lower = user_input.lower()
        intent_scores = {}
        
        # Score each intent based on pattern matching
        for intent, patterns in self.intent_patterns.items():
            score = 0.0
            
            # Check keyword patterns
            for pattern in patterns.get("keywords", []):
                if re.search(pattern, user_input_lower):
                    score += patterns.get("weight", 1.0)
            
            # Check phrase patterns
            for phrase in patterns.get("phrases", []):
                if phrase in user_input_lower:
                    score += patterns.get("weight", 1.0) * 1.5
            
            # Check exact matches
            for exact in patterns.get("exact_matches", []):
                if exact == user_input_lower.strip():
                    score += 10.0  # High score for exact matches
            
            if score > 0:
                intent_scores[intent] = score
        
        if not intent_scores:
            return UserIntent.GENERAL_INFORMATION, 0.3
        
        # Get highest scoring intent
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        intent_enum = UserIntent(best_intent[0])
        
        # Calculate confidence (normalized score)
        max_possible_score = 15.0  # Approximate maximum possible score
        confidence = min(best_intent[1] / max_possible_score, 1.0)
        
        return intent_enum, confidence
    
    async def _extract_entities(self, user_input: str, location_context: str = None) -> Dict:
        """
        Extract entities like locations, dates, and specific terms from user input
        """
        entities = {
            "locations": [],
            "dates": [],
            "health_conditions": [],
            "facility_types": [],
            "urgency_indicators": []
        }
        
        # Extract locations
        location_patterns = [
            r'\b([A-Z][a-z]+ (?:County|Parish))\b',  # County names
            r'\b([A-Z][a-z]+, [A-Z]{2})\b',         # City, State
            r'\b(California|Texas|New York|Florida|Illinois|Pennsylvania|Ohio|Georgia|North Carolina|Michigan)\b',  # States
            r'\b([A-Z][a-z]+ [A-Z][a-z]+(?:, [A-Z]{2})?)\b'  # City names
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            entities["locations"].extend(matches)
        
        # Add context location if provided
        if location_context:
            entities["locations"].append(location_context)
        
        # Extract dates and time references
        date_patterns = [
            r'\b(today|yesterday|tomorrow)\b',
            r'\b(this week|next week|last week)\b',
            r'\b(this month|next month|last month)\b',
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
            r'\b(\d{4}-\d{2}-\d{2})\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            entities["dates"].extend(matches)
        
        # Extract health conditions
        health_patterns = [
            r'\b(covid|coronavirus|influenza|flu|pneumonia)\b',
            r'\b(outbreak|epidemic|pandemic)\b',
            r'\b(symptoms|fever|cough|shortness of breath)\b'
        ]
        
        for pattern in health_patterns:
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            entities["health_conditions"].extend(matches)
        
        # Extract facility types
        facility_patterns = [
            r'\b(hospital|clinic|school|workplace|restaurant|gym)\b',
            r'\b(nursing home|long-term care|assisted living)\b',
            r'\b(airport|public transport|bus|train)\b'
        ]
        
        for pattern in facility_patterns:
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            entities["facility_types"].extend(matches)
        
        # Extract urgency indicators
        urgency_patterns = [
            r'\b(urgent|emergency|immediate|asap|critical)\b',
            r'\b(now|quickly|fast|rapid)\b'
        ]
        
        for pattern in urgency_patterns:
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            entities["urgency_indicators"].extend(matches)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    async def _determine_routing_strategy(self, intent: UserIntent, entities: Dict, 
                                        confidence: float) -> Dict:
        """
        Determine how to route the request based on intent and extracted entities
        """
        strategy = {
            "primary_agent": None,
            "workflow_type": "single_agent",
            "additional_agents": [],
            "parallel_processing": False,
            "priority_level": "normal"
        }
        
        # Determine urgency
        if entities.get("urgency_indicators") or confidence > 0.9:
            strategy["priority_level"] = "high"
        
        # Route based on intent
        if intent == UserIntent.OUTBREAK_STATUS:
            strategy.update({
                "primary_agent": "data_intelligence",
                "workflow_type": "full_analysis",
                "additional_agents": ["public_guidance"],
                "parallel_processing": False
            })
            
        elif intent == UserIntent.RISK_ASSESSMENT:
            strategy.update({
                "primary_agent": "data_intelligence",
                "workflow_type": "risk_focused",
                "additional_agents": [],
                "parallel_processing": False
            })
            
        elif intent == UserIntent.PUBLIC_GUIDANCE:
            strategy.update({
                "primary_agent": "public_guidance",
                "workflow_type": "guidance_focused",
                "additional_agents": ["data_intelligence"],
                "parallel_processing": False
            })
            
        elif intent in [UserIntent.SCHOOL_GUIDANCE, UserIntent.TRAVEL_GUIDANCE]:
            strategy.update({
                "primary_agent": "public_guidance",
                "workflow_type": "audience_specific",
                "additional_agents": ["data_intelligence"],
                "parallel_processing": False
            })
            
        elif intent in [UserIntent.RESOURCE_PLANNING, UserIntent.HOSPITAL_CAPACITY]:
            strategy.update({
                "primary_agent": "resource_planning",
                "workflow_type": "resource_focused",
                "additional_agents": ["data_intelligence"],
                "parallel_processing": False
            })
            
        elif intent == UserIntent.RUMOR_VALIDATION:
            strategy.update({
                "primary_agent": "data_intelligence",
                "workflow_type": "validation_focused",
                "additional_agents": [],
                "parallel_processing": False
            })
            
        elif intent == UserIntent.EMERGENCY_ALERT:
            strategy.update({
                "primary_agent": "orchestrator",
                "workflow_type": "emergency_response",
                "additional_agents": ["data_intelligence", "public_guidance", "resource_planning"],
                "parallel_processing": True,
                "priority_level": "critical"
            })
            
        else:  # GENERAL_INFORMATION
            strategy.update({
                "primary_agent": "orchestrator",
                "workflow_type": "general_inquiry",
                "additional_agents": ["data_intelligence"],
                "parallel_processing": False
            })
        
        # Adjust strategy based on entities
        if entities.get("facility_types"):
            if "hospital" in entities["facility_types"] or "clinic" in entities["facility_types"]:
                if "resource_planning" not in strategy["additional_agents"]:
                    strategy["additional_agents"].append("resource_planning")
        
        if len(entities.get("locations", [])) > 1:
            # Multiple locations require comparative analysis
            strategy["workflow_type"] = "comparative_analysis"
        
        return strategy
    
    def _load_intent_patterns(self) -> Dict:
        """
        Load intent classification patterns and keywords
        """
        return {
            "outbreak_status": {
                "keywords": [
                    r'\boutbreak\b', r'\bspread\b', r'\bcases\b', r'\bincreasing\b',
                    r'\bstatus\b', r'\bsituation\b', r'\bcurrent\b'
                ],
                "phrases": [
                    "outbreak status", "current situation", "case numbers",
                    "is there an outbreak", "outbreak activity", "infection rate"
                ],
                "weight": 2.0
            },
            
            "risk_assessment": {
                "keywords": [
                    r'\brisk\b', r'\bdanger\b', r'\bthreat\b', r'\bassess\b',
                    r'\bsafety\b', r'\bscore\b'
                ],
                "phrases": [
                    "risk level", "how dangerous", "threat assessment",
                    "risk score", "safety level"
                ],
                "weight": 2.0
            },
            
            "public_guidance": {
                "keywords": [
                    r'\bguidance\b', r'\brecommend\b', r'\badvice\b', r'\bshould\b',
                    r'\bprotection\b', r'\bprecaution\b'
                ],
                "phrases": [
                    "public guidance", "recommendations", "what should",
                    "health advice", "safety measures", "precautions"
                ],
                "weight": 2.0
            },
            
            "school_guidance": {
                "keywords": [
                    r'\bschool\b', r'\bstudent\b', r'\beducation\b', r'\bclass\b',
                    r'\bteacher\b', r'\bcampus\b'
                ],
                "phrases": [
                    "school safety", "student guidance", "classroom precautions",
                    "school closure", "educational settings"
                ],
                "weight": 2.5
            },
            
            "travel_guidance": {
                "keywords": [
                    r'\btravel\b', r'\btrip\b', r'\bflight\b', r'\btransport\b',
                    r'\bairport\b', r'\bvisit\b'
                ],
                "phrases": [
                    "travel advice", "travel restrictions", "safe to travel",
                    "travel guidance", "trip safety"
                ],
                "weight": 2.5
            },
            
            "resource_planning": {
                "keywords": [
                    r'\bresource\b', r'\bsupply\b', r'\bcapacity\b', r'\bbed\b',
                    r'\bppe\b', r'\bequipment\b', r'\bshortage\b'
                ],
                "phrases": [
                    "resource allocation", "hospital capacity", "bed availability",
                    "ppe shortage", "medical supplies", "resource planning"
                ],
                "weight": 2.0
            },
            
            "hospital_capacity": {
                "keywords": [
                    r'\bhospital\b', r'\bicu\b', r'\bbed\b', r'\bcapacity\b',
                    r'\bavailable\b', r'\bfull\b'
                ],
                "phrases": [
                    "hospital capacity", "icu availability", "bed shortage",
                    "hospital full", "medical capacity"
                ],
                "weight": 2.5
            },
            
            "rumor_validation": {
                "keywords": [
                    r'\brumor\b', r'\bheard\b', r'\btrue\b', r'\bfalse\b',
                    r'\bverify\b', r'\bcheck\b', r'\bclaim\b'
                ],
                "phrases": [
                    "is it true", "verify claim", "fact check", "rumor validation",
                    "heard that", "check if"
                ],
                "weight": 2.0
            },
            
            "emergency_alert": {
                "keywords": [
                    r'\bemergency\b', r'\bcrisis\b', r'\burgent\b', r'\bcritical\b',
                    r'\balert\b', r'\bimmediate\b'
                ],
                "phrases": [
                    "emergency alert", "crisis situation", "urgent response",
                    "critical outbreak", "immediate action"
                ],
                "weight": 3.0
            },
            
            "general_information": {
                "keywords": [
                    r'\bwhat\b', r'\bhow\b', r'\bwhen\b', r'\bwhere\b',
                    r'\binfo\b', r'\bhelp\b'
                ],
                "phrases": [
                    "general information", "tell me about", "help with",
                    "information about"
                ],
                "weight": 1.0
            }
        }
    
    def _create_fallback_routing(self, user_input: str, location: str) -> Dict:
        """
        Create fallback routing when intent classification fails
        """
        return {
            "intent": "general_information",
            "confidence": 0.1,
            "entities": {"locations": [location] if location else []},
            "routing_strategy": {
                "primary_agent": "orchestrator",
                "workflow_type": "general_inquiry",
                "additional_agents": ["data_intelligence"],
                "parallel_processing": False,
                "priority_level": "normal"
            },
            "user_input": user_input,
            "processing_timestamp": self._get_timestamp(),
            "fallback": True
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def get_routing_confidence_explanation(self, routing_result: Dict) -> str:
        """
        Provide explanation of routing decision for transparency
        """
        intent = routing_result["intent"]
        confidence = routing_result["confidence"]
        entities = routing_result["entities"]
        
        explanation = f"Intent classified as '{intent}' with {confidence:.1%} confidence. "
        
        if entities.get("locations"):
            explanation += f"Detected locations: {', '.join(entities['locations'])}. "
        
        if entities.get("urgency_indicators"):
            explanation += "Urgency indicators detected. "
        
        strategy = routing_result["routing_strategy"]
        explanation += f"Routing to {strategy['primary_agent']} agent using {strategy['workflow_type']} workflow."
        
        if strategy["additional_agents"]:
            explanation += f" Additional agents: {', '.join(strategy['additional_agents'])}."
        
        return explanation