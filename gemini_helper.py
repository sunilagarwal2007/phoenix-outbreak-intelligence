"""
Phoenix Outbreak Intelligence - Gemini AI Helper
Utility functions for using Google's Gemini AI via Vertex AI
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig, Part
from google.cloud import aiplatform

logger = logging.getLogger(__name__)


class GeminiAIHelper:
    """Helper class for Google Gemini AI integration"""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        model_name: str = "gemini-2.5-flash"
    ):
        """
        Initialize Gemini AI helper
        
        Args:
            project_id: GCP project ID (defaults to environment variable)
            location: GCP region (default: us-central1)
            model_name: Gemini model to use (default: gemini-2.5-flash)
        """
        self.project_id = project_id or os.getenv('PROJECT_ID')
        self.location = location or os.getenv('VERTEX_AI_LOCATION', 'us-central1')
        self.model_name = model_name or os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        
        if not self.project_id:
            raise ValueError("PROJECT_ID must be set in environment or passed to constructor")
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)
        
        # Initialize the model
        self.model = GenerativeModel(self.model_name)
        
        logger.info(f"Initialized Gemini AI with model: {self.model_name}")
    
    def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 4096,
        top_p: float = 0.95,
        top_k: int = 40
    ) -> str:
        """
        Generate text using Gemini AI
        
        Args:
            prompt: Input prompt
            temperature: Creativity (0.0-1.0, higher = more creative)
            max_output_tokens: Maximum response length
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            
        Returns:
            Generated text response
        """
        try:
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                top_p=top_p,
                top_k=top_k
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {e}")
            raise
    
    def generate_structured_output(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output using Gemini AI
        
        Args:
            prompt: Input prompt
            output_schema: JSON schema for expected output
            temperature: Lower temperature for more consistent structured output
            
        Returns:
            Parsed JSON response
        """
        try:
            # Add schema to prompt
            schema_prompt = f"""{prompt}

Please respond with valid JSON matching this schema:
{json.dumps(output_schema, indent=2)}

Only return the JSON, no additional text."""
            
            response = self.generate_text(
                schema_prompt,
                temperature=temperature,
                max_output_tokens=4096
            )
            
            # Extract JSON from response
            response_text = response.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            return json.loads(response_text.strip())
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response}")
            raise
        except Exception as e:
            logger.error(f"Error generating structured output: {e}")
            raise
    
    def analyze_with_context(
        self,
        query: str,
        context: str,
        temperature: float = 0.7
    ) -> str:
        """
        Analyze a query with given context
        
        Args:
            query: User query
            context: Context information
            temperature: Generation temperature
            
        Returns:
            Analysis result
        """
        prompt = f"""Context:
{context}

Query: {query}

Please provide a detailed analysis based on the context provided."""
        
        return self.generate_text(prompt, temperature=temperature)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> str:
        """
        Multi-turn chat conversation
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Generation temperature
            
        Returns:
            Assistant's response
        """
        try:
            # Convert messages to Gemini format
            chat = self.model.start_chat()
            
            # Send all messages except the last one as history
            for msg in messages[:-1]:
                if msg['role'] == 'user':
                    chat.send_message(msg['content'])
            
            # Send the last message and get response
            last_message = messages[-1]['content']
            response = chat.send_message(last_message)
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            raise


# Convenience functions for common use cases

def analyze_outbreak_risk_with_gemini(
    location: str,
    case_data: Dict[str, Any],
    hospital_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Use Gemini to analyze outbreak risk
    
    Args:
        location: Geographic location
        case_data: COVID/flu case statistics
        hospital_data: Hospital capacity data
        
    Returns:
        Risk analysis with score and recommendations
    """
    gemini = GeminiAIHelper()
    
    prompt = f"""Analyze the following outbreak data for {location}:

Case Data:
{json.dumps(case_data, indent=2)}

Hospital Data:
{json.dumps(hospital_data, indent=2)}

Provide a comprehensive risk analysis including:
1. Overall risk score (0-100)
2. Risk level (LOW, MODERATE, HIGH, CRITICAL)
3. Key trends and patterns
4. Actionable recommendations
5. Confidence level (0-100)"""
    
    schema = {
        "risk_score": "number (0-100)",
        "risk_level": "string (LOW|MODERATE|HIGH|CRITICAL)",
        "trends": {
            "cases": "object with trend analysis",
            "hospitals": "object with capacity analysis"
        },
        "recommendations": ["array of strings"],
        "confidence": "number (0-100)"
    }
    
    return gemini.generate_structured_output(prompt, schema, temperature=0.3)


def generate_public_guidance_with_gemini(
    risk_level: str,
    location: str,
    target_audience: str = "general_public"
) -> Dict[str, Any]:
    """
    Use Gemini to generate public health guidance
    
    Args:
        risk_level: Current risk level
        location: Geographic location
        target_audience: Who the guidance is for
        
    Returns:
        Formatted public health guidance
    """
    gemini = GeminiAIHelper()
    
    prompt = f"""Generate clear, actionable public health guidance for {target_audience} in {location}.

Current Risk Level: {risk_level}

The guidance should include:
1. A clear headline
2. 3-5 key actions people should take
3. Detailed explanation
4. Urgency level (LOW, MODERATE, HIGH)
5. Tone appropriate for the audience"""
    
    schema = {
        "headline": "string",
        "key_actions": ["array of strings"],
        "detailed_guidance": "string",
        "urgency": "string (LOW|MODERATE|HIGH)",
        "tone": "string"
    }
    
    return gemini.generate_structured_output(prompt, schema, temperature=0.5)


def analyze_resource_needs_with_gemini(
    location: str,
    current_capacity: Dict[str, Any],
    projected_demand: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Use Gemini to analyze healthcare resource needs
    
    Args:
        location: Geographic location
        current_capacity: Current resource availability
        projected_demand: Projected future demand
        
    Returns:
        Resource analysis with recommendations
    """
    gemini = GeminiAIHelper()
    
    prompt = f"""Analyze healthcare resource needs for {location}.

Current Capacity:
{json.dumps(current_capacity, indent=2)}

Projected Demand (14 days):
{json.dumps(projected_demand, indent=2)}

Provide:
1. Resource deficit calculations
2. Prioritized procurement recommendations
3. Cost estimates
4. Timeline recommendations
5. Risk assessment if needs aren't met"""
    
    schema = {
        "resource_needs": {
            "icu_beds": "object with deficit and recommendations",
            "ventilators": "object with deficit and recommendations",
            "staff": "object with deficit and recommendations"
        },
        "procurement_recommendations": ["array of recommendation objects"],
        "total_estimated_cost": "number",
        "timeline": "string",
        "risk_if_unmet": "string"
    }
    
    return gemini.generate_structured_output(prompt, schema, temperature=0.3)


# Example usage
if __name__ == "__main__":
    # Initialize
    gemini = GeminiAIHelper()
    
    # Simple text generation
    response = gemini.generate_text("Explain the importance of outbreak intelligence systems.")
    print(f"Response: {response}")
    
    # Structured output
    risk_analysis = analyze_outbreak_risk_with_gemini(
        location="California",
        case_data={"daily_cases": 1500, "growth_rate": 0.15},
        hospital_data={"icu_occupancy": 0.87, "available_beds": 189}
    )
    print(f"Risk Analysis: {json.dumps(risk_analysis, indent=2)}")
