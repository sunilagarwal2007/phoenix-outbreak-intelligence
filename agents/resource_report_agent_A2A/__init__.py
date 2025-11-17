"""
Resource Report Agent (A2A) package for Phoenix Outbreak Intelligence
"""

from .agent import ResourceReportAgent, ResourceRequirement, FacilityAssessment
from .prompts import (
    SYSTEM_PROMPT,
    RESOURCE_PROJECTION_PROMPT,
    FACILITY_ASSESSMENT_PROMPT,
    COST_ANALYSIS_PROMPT,
    PROCUREMENT_RECOMMENDATION_PROMPT,
    REPORT_TEMPLATES
)

__all__ = [
    'ResourceReportAgent',
    'ResourceRequirement',
    'FacilityAssessment',
    'SYSTEM_PROMPT',
    'RESOURCE_PROJECTION_PROMPT',
    'FACILITY_ASSESSMENT_PROMPT',
    'COST_ANALYSIS_PROMPT',
    'PROCUREMENT_RECOMMENDATION_PROMPT',
    'REPORT_TEMPLATES'
]

__version__ = "1.0.0"