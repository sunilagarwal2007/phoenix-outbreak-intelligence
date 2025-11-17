"""
Public Guidance Agent package for Phoenix Outbreak Intelligence
"""

from .agent import PublicGuidanceAgent, GuidanceRecommendation
from .prompts import (
    SYSTEM_PROMPT,
    GUIDANCE_GENERATION_PROMPT,
    RISK_LEVEL_TEMPLATES,
    AUDIENCE_SPECIFIC_PROMPTS,
    MESSAGE_TEMPLATES
)

__all__ = [
    'PublicGuidanceAgent',
    'GuidanceRecommendation',
    'SYSTEM_PROMPT',
    'GUIDANCE_GENERATION_PROMPT',
    'RISK_LEVEL_TEMPLATES',
    'AUDIENCE_SPECIFIC_PROMPTS',
    'MESSAGE_TEMPLATES'
]

__version__ = "1.0.0"