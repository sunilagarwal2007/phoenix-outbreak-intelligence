"""
Data Intelligence Agent package for Phoenix Outbreak Intelligence
"""

from .agent import DataIntelligenceAgent
from .prompts import (
    SYSTEM_PROMPT,
    BIGQUERY_ANALYSIS_PROMPT,
    RISK_SCORING_PROMPT,
    RUMOR_VALIDATION_PROMPT,
    QUERY_TEMPLATES,
    RESPONSE_TEMPLATES
)

__all__ = [
    'DataIntelligenceAgent',
    'SYSTEM_PROMPT',
    'BIGQUERY_ANALYSIS_PROMPT', 
    'RISK_SCORING_PROMPT',
    'RUMOR_VALIDATION_PROMPT',
    'QUERY_TEMPLATES',
    'RESPONSE_TEMPLATES'
]

__version__ = "1.0.0"