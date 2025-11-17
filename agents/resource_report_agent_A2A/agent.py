"""
Resource Report Agent (A2A) for Phoenix Outbreak Intelligence
Cloud Run-deployed agent for generating resource allocation reports and PDF outputs
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import asyncio
from pathlib import Path
import sys

# Add parent directory to path to import gemini_helper
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from gemini_helper import GeminiAIHelper, analyze_resource_needs_with_gemini

@dataclass
class ResourceRequirement:
    """Structure for resource allocation requirements"""
    resource_type: str  # "icu_beds", "ppe", "testing_capacity", "staff"
    current_capacity: int
    projected_need: int
    shortage_amount: int
    priority_level: str  # "CRITICAL", "HIGH", "MODERATE", "LOW"
    estimated_cost: float
    procurement_timeline: str
    alternative_sources: List[str]

@dataclass
class FacilityAssessment:
    """Assessment of individual healthcare facility"""
    facility_id: str
    facility_name: str
    facility_type: str  # "hospital", "clinic", "testing_center"
    current_capacity: Dict[str, int]
    utilization_rate: float
    projected_demand: Dict[str, int]
    resource_gaps: List[ResourceRequirement]
    geographic_coordinates: Tuple[float, float]
    contact_info: Dict[str, str]

class ResourceReportAgent:
    """
    A2A (Agent-to-Agent) Resource Report Agent deployed on Cloud Run
    
    Responsibilities:
    - Generate comprehensive resource allocation reports
    - Calculate ICU bed, PPE, and testing capacity needs
    - Create PDF reports with visualizations
    - Provide facility-level assessments
    - Generate procurement recommendations
    - Interface with Google Maps MCP for routing optimization
    """
    
    def __init__(self, project_id: str, maps_api_key: Optional[str] = None):
        self.project_id = project_id
        self.maps_api_key = maps_api_key
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gemini AI for resource analysis
        try:
            self.gemini = GeminiAIHelper(project_id=project_id)
            self.logger.info("Gemini AI initialized successfully")
        except Exception as e:
            self.logger.warning(f"Could not initialize Gemini AI: {e}")
            self.gemini = None
        
    async def generate_resource_report(self, risk_analysis: Dict, location: str,
                                     forecast_days: int = 14) -> Dict:
        """
        Main function to generate comprehensive resource allocation report
        
        Args:
            risk_analysis: Output from DataIntelligenceAgent
            location: Geographic area for resource planning
            forecast_days: Number of days to forecast resource needs
            
        Returns:
            Dict containing complete resource allocation analysis
        """
        try:
            risk_score = risk_analysis.get("risk_score", 0)
            growth_rate = self._extract_growth_rate(risk_analysis)
            
            # Assess current facility status
            facilities = await self._assess_healthcare_facilities(location)
            
            # Calculate resource projections
            resource_projections = await self._calculate_resource_projections(
                facilities, risk_score, growth_rate, forecast_days
            )
            
            # Generate specific recommendations
            recommendations = await self._generate_procurement_recommendations(
                resource_projections
            )
            
            # Calculate costs and timelines
            cost_analysis = self._calculate_cost_projections(resource_projections)
            
            # Generate geographic optimization
            logistics_plan = await self._optimize_resource_distribution(
                facilities, resource_projections
            )
            
            report = {
                "report_id": f"PHX-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "location": location,
                "generation_date": datetime.now().isoformat(),
                "forecast_period": f"{forecast_days} days",
                "risk_context": {
                    "risk_score": risk_score,
                    "growth_rate": growth_rate,
                    "confidence": risk_analysis.get("confidence", 0.8)
                },
                "facility_assessments": [facility.__dict__ for facility in facilities],
                "resource_projections": resource_projections,
                "procurement_recommendations": recommendations,
                "cost_analysis": cost_analysis,
                "logistics_plan": logistics_plan,
                "executive_summary": self._create_executive_summary(
                    resource_projections, cost_analysis
                )
            }
            
            # Generate PDF if requested
            pdf_path = await self._generate_pdf_report(report)
            report["pdf_report_path"] = pdf_path
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating resource report: {str(e)}")
            raise
    
    async def _assess_healthcare_facilities(self, location: str) -> List[FacilityAssessment]:
        """Assess current status of healthcare facilities in the area"""
        # In a real implementation, this would query:
        # - Hospital management systems
        # - State health department databases
        # - CMS provider data
        
        # Mock data for demonstration
        facilities = [
            FacilityAssessment(
                facility_id="HOSP-001",
                facility_name="General Hospital",
                facility_type="hospital",
                current_capacity={
                    "icu_beds": 50,
                    "medical_beds": 200,
                    "ventilators": 45,
                    "testing_capacity_daily": 500
                },
                utilization_rate=0.78,
                projected_demand={},  # Will be calculated
                resource_gaps=[],     # Will be calculated
                geographic_coordinates=(37.7749, -122.4194),  # Example coords
                contact_info={
                    "emergency_contact": "555-0101",
                    "logistics_contact": "555-0102"
                }
            ),
            FacilityAssessment(
                facility_id="CLINIC-001", 
                facility_name="Community Health Center",
                facility_type="clinic",
                current_capacity={
                    "testing_capacity_daily": 200,
                    "urgent_care_beds": 10
                },
                utilization_rate=0.65,
                projected_demand={},
                resource_gaps=[],
                geographic_coordinates=(37.7849, -122.4094),
                contact_info={
                    "emergency_contact": "555-0201"
                }
            )
        ]
        
        return facilities
    
    async def _calculate_resource_projections(self, facilities: List[FacilityAssessment],
                                            risk_score: float, growth_rate: float,
                                            forecast_days: int) -> Dict:
        """Calculate projected resource needs based on outbreak trajectory"""
        
        # Base demand multipliers based on risk score
        demand_multipliers = {
            "icu_beds": 1.0 + (risk_score / 100) * 2.0,
            "medical_beds": 1.0 + (risk_score / 100) * 1.5,
            "ventilators": 1.0 + (risk_score / 100) * 1.8,
            "testing_capacity": 1.0 + (risk_score / 100) * 3.0,
            "ppe_daily": 1.0 + (risk_score / 100) * 4.0,
            "staff": 1.0 + (risk_score / 100) * 1.3
        }
        
        # Calculate total current capacity
        total_capacity = {
            "icu_beds": sum(f.current_capacity.get("icu_beds", 0) for f in facilities),
            "medical_beds": sum(f.current_capacity.get("medical_beds", 0) for f in facilities),
            "ventilators": sum(f.current_capacity.get("ventilators", 0) for f in facilities),
            "testing_capacity_daily": sum(f.current_capacity.get("testing_capacity_daily", 0) for f in facilities)
        }
        
        # Project needs considering growth rate
        projections = {}
        for resource, base_capacity in total_capacity.items():
            current_demand = base_capacity * 0.8  # Assume 80% baseline utilization
            
            # Apply risk-based demand increase
            elevated_demand = current_demand * demand_multipliers.get(resource, 1.0)
            
            # Apply growth rate over forecast period
            final_demand = elevated_demand * (1 + growth_rate) ** (forecast_days / 7)
            
            shortage = max(0, final_demand - base_capacity)
            
            projections[resource] = {
                "current_capacity": base_capacity,
                "current_demand": current_demand,
                "projected_demand": final_demand,
                "shortage": shortage,
                "utilization_projected": min(1.0, final_demand / base_capacity),
                "priority": self._calculate_priority(shortage, base_capacity)
            }
        
        # Calculate PPE needs (not tied to bed capacity)
        daily_ppe_needs = self._calculate_ppe_requirements(
            projections["icu_beds"]["projected_demand"],
            projections["medical_beds"]["projected_demand"],
            risk_score
        )
        
        projections["ppe"] = daily_ppe_needs
        
        return projections
    
    def _calculate_ppe_requirements(self, icu_demand: float, med_demand: float,
                                   risk_score: float) -> Dict:
        """Calculate PPE requirements based on patient load and risk level"""
        
        # PPE consumption rates per patient per day
        ppe_rates = {
            "n95_masks": 3,
            "surgical_masks": 6,
            "gowns": 4,
            "gloves_pairs": 12,
            "face_shields": 1,
            "sanitizer_bottles": 0.1
        }
        
        # Risk-based multipliers
        risk_multiplier = 1.0 + (risk_score / 100) * 2.0
        
        total_patients = icu_demand + med_demand
        
        ppe_needs = {}
        for ppe_type, rate in ppe_rates.items():
            daily_need = total_patients * rate * risk_multiplier
            
            ppe_needs[ppe_type] = {
                "daily_consumption": daily_need,
                "weekly_need": daily_need * 7,
                "monthly_need": daily_need * 30,
                "strategic_reserve": daily_need * 90,  # 90-day reserve
                "estimated_cost_weekly": self._get_ppe_cost(ppe_type, daily_need * 7)
            }
        
        return ppe_needs
    
    def _get_ppe_cost(self, ppe_type: str, quantity: float) -> float:
        """Estimate PPE costs based on current market rates"""
        cost_per_unit = {
            "n95_masks": 1.50,
            "surgical_masks": 0.25,
            "gowns": 2.00,
            "gloves_pairs": 0.15,
            "face_shields": 3.00,
            "sanitizer_bottles": 4.00
        }
        
        return quantity * cost_per_unit.get(ppe_type, 1.0)
    
    async def _generate_procurement_recommendations(self, projections: Dict) -> List[Dict]:
        """Generate specific procurement recommendations with timelines"""
        recommendations = []
        
        for resource, projection in projections.items():
            if resource == "ppe":
                # Handle PPE separately due to different structure
                for ppe_type, ppe_data in projection.items():
                    if ppe_data.get("weekly_need", 0) > 1000:  # Significant need threshold
                        recommendations.append({
                            "resource": f"{ppe_type}",
                            "quantity_needed": ppe_data["monthly_need"],
                            "timeline": "Immediate (1-3 days)",
                            "estimated_cost": ppe_data["estimated_cost_weekly"] * 4,
                            "procurement_strategy": "Emergency procurement + strategic reserve",
                            "alternative_suppliers": ["Supplier A", "Supplier B", "Federal stockpile"]
                        })
            else:
                shortage = projection.get("shortage", 0)
                if shortage > 0:
                    recommendations.append({
                        "resource": resource,
                        "quantity_needed": shortage,
                        "timeline": self._get_procurement_timeline(resource, shortage),
                        "estimated_cost": self._estimate_resource_cost(resource, shortage),
                        "procurement_strategy": self._get_procurement_strategy(resource),
                        "alternative_suppliers": self._get_alternative_suppliers(resource)
                    })
        
        return sorted(recommendations, key=lambda x: self._get_priority_score(x))
    
    def _get_procurement_timeline(self, resource: str, quantity: float) -> str:
        """Estimate procurement timeline based on resource type and quantity"""
        timelines = {
            "icu_beds": "2-4 weeks (temporary units)",
            "medical_beds": "1-2 weeks", 
            "ventilators": "1-3 weeks",
            "testing_capacity_daily": "3-7 days (mobile units)"
        }
        
        base_timeline = timelines.get(resource, "1-2 weeks")
        
        # Adjust for large quantities
        if quantity > 100:
            return f"{base_timeline} + extended delivery"
        
        return base_timeline
    
    def _estimate_resource_cost(self, resource: str, quantity: float) -> float:
        """Estimate costs for major resource procurements"""
        unit_costs = {
            "icu_beds": 15000,  # Including monitoring equipment
            "medical_beds": 3000,
            "ventilators": 25000,
            "testing_capacity_daily": 50000  # Mobile testing unit
        }
        
        return quantity * unit_costs.get(resource, 5000)
    
    def _get_procurement_strategy(self, resource: str) -> str:
        """Define procurement strategy based on resource type"""
        strategies = {
            "icu_beds": "Temporary unit deployment + equipment rental",
            "medical_beds": "Existing facility expansion + field hospitals",
            "ventilators": "Emergency purchase + federal reserve activation",
            "testing_capacity_daily": "Mobile unit deployment + lab partnerships"
        }
        
        return strategies.get(resource, "Standard procurement process")
    
    def _get_alternative_suppliers(self, resource: str) -> List[str]:
        """Identify alternative suppliers for resources"""
        suppliers = {
            "icu_beds": ["Medical Equipment Co.", "Emergency Response Supply", "Federal Reserve"],
            "medical_beds": ["Hospital Supply Inc.", "Emergency Medical", "State Stockpile"],
            "ventilators": ["Ventilator Manufacturer A", "Medical Device Co.", "National Reserve"],
            "testing_capacity_daily": ["Lab Corp", "Quest Diagnostics", "Mobile Testing Inc."]
        }
        
        return suppliers.get(resource, ["Standard Suppliers"])
    
    def _calculate_priority(self, shortage: float, capacity: float) -> str:
        """Calculate priority level based on shortage severity"""
        if capacity == 0:
            return "LOW"
        
        shortage_ratio = shortage / capacity
        
        if shortage_ratio > 0.5:
            return "CRITICAL"
        elif shortage_ratio > 0.25:
            return "HIGH"  
        elif shortage_ratio > 0.1:
            return "MODERATE"
        else:
            return "LOW"
    
    def _get_priority_score(self, recommendation: Dict) -> int:
        """Score recommendations for priority sorting"""
        priority_scores = {"CRITICAL": 4, "HIGH": 3, "MODERATE": 2, "LOW": 1}
        
        # Extract priority from resource analysis or default
        priority = "MODERATE"  # Default priority
        return priority_scores.get(priority, 2)
    
    def _calculate_cost_projections(self, projections: Dict) -> Dict:
        """Calculate comprehensive cost analysis"""
        total_costs = {
            "immediate_needs": 0,
            "short_term": 0,
            "long_term": 0
        }
        
        cost_breakdown = {}
        
        # Calculate costs for each resource category
        for resource, projection in projections.items():
            if resource == "ppe":
                # Sum PPE costs
                weekly_ppe_cost = sum(
                    ppe_data.get("estimated_cost_weekly", 0) 
                    for ppe_data in projection.values()
                )
                cost_breakdown["ppe"] = {
                    "weekly": weekly_ppe_cost,
                    "monthly": weekly_ppe_cost * 4,
                    "quarterly": weekly_ppe_cost * 13
                }
                total_costs["immediate_needs"] += weekly_ppe_cost * 2
                total_costs["short_term"] += weekly_ppe_cost * 8
            else:
                shortage = projection.get("shortage", 0)
                if shortage > 0:
                    resource_cost = self._estimate_resource_cost(resource, shortage)
                    cost_breakdown[resource] = resource_cost
                    total_costs["immediate_needs"] += resource_cost
        
        return {
            "total_costs": total_costs,
            "cost_breakdown": cost_breakdown,
            "funding_recommendations": self._generate_funding_recommendations(total_costs)
        }
    
    def _generate_funding_recommendations(self, costs: Dict) -> List[str]:
        """Generate funding source recommendations"""
        recommendations = []
        
        immediate = costs["immediate_needs"]
        
        if immediate > 1000000:
            recommendations.append("Federal emergency funding request")
            recommendations.append("State disaster relief funds")
        elif immediate > 500000:
            recommendations.append("State emergency allocation")
            recommendations.append("Regional healthcare consortium funding")
        elif immediate > 100000:
            recommendations.append("Local emergency funds")
            recommendations.append("Hospital system reserves")
        else:
            recommendations.append("Standard operational budget")
        
        return recommendations
    
    async def _optimize_resource_distribution(self, facilities: List[FacilityAssessment],
                                            projections: Dict) -> Dict:
        """Optimize resource distribution using geographic analysis"""
        # This would integrate with Google Maps MCP for routing
        # Mock implementation for demonstration
        
        distribution_plan = {
            "delivery_zones": [],
            "routing_optimization": {},
            "logistics_timeline": "2-5 days for full deployment"
        }
        
        for facility in facilities:
            zone = {
                "facility": facility.facility_name,
                "coordinates": facility.geographic_coordinates,
                "priority": self._calculate_facility_priority(facility),
                "estimated_delivery_time": "24-48 hours",
                "access_considerations": "Standard urban delivery"
            }
            distribution_plan["delivery_zones"].append(zone)
        
        return distribution_plan
    
    def _calculate_facility_priority(self, facility: FacilityAssessment) -> str:
        """Calculate delivery priority for facilities"""
        if facility.utilization_rate > 0.9:
            return "CRITICAL"
        elif facility.utilization_rate > 0.8:
            return "HIGH"
        elif facility.utilization_rate > 0.7:
            return "MODERATE"
        else:
            return "LOW"
    
    def _extract_growth_rate(self, risk_analysis: Dict) -> float:
        """Extract growth rate from risk analysis data"""
        trends = risk_analysis.get("trends", {})
        case_data = trends.get("cases", {})
        return case_data.get("growth_rate", 0.1)  # Default 10% growth
    
    def _create_executive_summary(self, projections: Dict, costs: Dict) -> str:
        """Create executive summary of the resource report"""
        critical_shortages = []
        total_cost = costs["total_costs"]["immediate_needs"]
        
        for resource, projection in projections.items():
            if resource != "ppe":
                priority = projection.get("priority", "LOW")
                if priority in ["CRITICAL", "HIGH"]:
                    shortage = projection.get("shortage", 0)
                    critical_shortages.append(f"{resource}: {shortage:.0f} units")
        
        # Use Gemini AI for executive summary if available
        if self.gemini:
            try:
                prompt = f"""Create an executive summary for a healthcare resource allocation report.

Critical Shortages: {critical_shortages if critical_shortages else "None"}
Total Immediate Cost: ${total_cost:,.2f}
Projections: {json.dumps(projections, indent=2)[:1000]}  # Truncated for context

Generate a concise executive summary (200-300 words) that includes:
1. Situation overview
2. Critical resource gaps
3. Financial impact
4. Top 3-4 actionable recommendations
5. Urgency assessment

Use professional tone appropriate for healthcare executives and government officials."""
                
                gemini_summary = self.gemini.generate_text(prompt, temperature=0.3, max_output_tokens=2048)
                
                return f"""EXECUTIVE SUMMARY - RESOURCE ALLOCATION REPORT

{gemini_summary}

Report generated: {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}"""
                
            except Exception as e:
                self.logger.warning(f"Gemini summary generation failed: {e}, using template")
        
        # Fallback to template-based summary
        summary = f"""
EXECUTIVE SUMMARY - RESOURCE ALLOCATION REPORT

Critical Resource Shortages Identified:
{chr(10).join(f"• {shortage}" for shortage in critical_shortages) if critical_shortages else "• No critical shortages projected"}

Estimated Immediate Funding Need: ${total_cost:,.2f}

Key Recommendations:
• Activate emergency procurement procedures
• Coordinate with regional healthcare consortium
• Establish supply chain partnerships
• Monitor and adjust projections daily

Report generated: {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}
        """
        
        return summary.strip()
    
    async def _generate_pdf_report(self, report: Dict) -> str:
        """Generate PDF version of the resource report"""
        # This would use reportlab or similar to generate PDF
        # Mock implementation returns file path
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resource_report_{timestamp}.pdf"
        filepath = f"/tmp/{filename}"
        
        # In real implementation, would generate actual PDF with:
        # - Executive summary
        # - Charts and visualizations
        # - Facility assessments
        # - Procurement recommendations
        # - Cost analysis
        
        self.logger.info(f"PDF report would be generated at: {filepath}")
        
        return filepath