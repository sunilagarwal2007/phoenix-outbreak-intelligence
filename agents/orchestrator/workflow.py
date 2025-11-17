"""
Orchestrator Workflow for Phoenix Outbreak Intelligence
Main workflow coordination between all specialized agents
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio
from enum import Enum

class WorkflowStage(Enum):
    """Workflow stages for outbreak response"""
    INITIALIZATION = "initialization"
    DATA_COLLECTION = "data_collection"
    RISK_ASSESSMENT = "risk_assessment"
    GUIDANCE_GENERATION = "guidance_generation"
    RESOURCE_PLANNING = "resource_planning"
    REPORT_COMPILATION = "report_compilation"
    FINALIZATION = "finalization"

class PhoenixWorkflow:
    """
    Main workflow orchestrator that coordinates all Phoenix agents
    Implements the complete outbreak intelligence pipeline
    """
    
    def __init__(self, data_agent, guidance_agent, resource_agent):
        self.data_agent = data_agent
        self.guidance_agent = guidance_agent
        self.resource_agent = resource_agent
        self.logger = logging.getLogger(__name__)
        self.workflow_state = {}
        
    async def execute_full_analysis(self, location: str, target_audience: str = "general_public",
                                  generate_pdf: bool = True) -> Dict:
        """
        Execute complete outbreak intelligence analysis
        
        Args:
            location: Geographic location for analysis
            target_audience: Target audience for guidance
            generate_pdf: Whether to generate PDF reports
            
        Returns:
            Complete analysis results with all agent outputs
        """
        workflow_id = f"PHX-WF-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        try:
            self.logger.info(f"Starting Phoenix workflow {workflow_id} for {location}")
            
            # Stage 1: Initialize workflow
            await self._update_stage(workflow_id, WorkflowStage.INITIALIZATION)
            workflow_context = await self._initialize_workflow(workflow_id, location)
            
            # Stage 2: Data Collection & Risk Assessment
            await self._update_stage(workflow_id, WorkflowStage.DATA_COLLECTION)
            risk_analysis = await self._execute_risk_assessment(location)
            
            # Stage 3: Generate Public Guidance  
            await self._update_stage(workflow_id, WorkflowStage.GUIDANCE_GENERATION)
            guidance_results = await self._generate_public_guidance(
                risk_analysis, location, target_audience
            )
            
            # Stage 4: Resource Planning
            await self._update_stage(workflow_id, WorkflowStage.RESOURCE_PLANNING)
            resource_report = await self._generate_resource_report(
                risk_analysis, location, generate_pdf
            )
            
            # Stage 5: Compile Final Report
            await self._update_stage(workflow_id, WorkflowStage.REPORT_COMPILATION)
            final_report = await self._compile_final_report(
                workflow_id, risk_analysis, guidance_results, resource_report
            )
            
            # Stage 6: Finalization
            await self._update_stage(workflow_id, WorkflowStage.FINALIZATION)
            await self._finalize_workflow(workflow_id, final_report)
            
            self.logger.info(f"Phoenix workflow {workflow_id} completed successfully")
            return final_report
            
        except Exception as e:
            self.logger.error(f"Phoenix workflow {workflow_id} failed: {str(e)}")
            await self._handle_workflow_error(workflow_id, e)
            raise
    
    async def _initialize_workflow(self, workflow_id: str, location: str) -> Dict:
        """Initialize workflow context and validate inputs"""
        context = {
            "workflow_id": workflow_id,
            "location": location,
            "start_time": datetime.now().isoformat(),
            "agents_available": {
                "data_intelligence": self.data_agent is not None,
                "public_guidance": self.guidance_agent is not None,
                "resource_planning": self.resource_agent is not None
            }
        }
        
        self.workflow_state[workflow_id] = context
        
        # Validate all required agents are available
        if not all(context["agents_available"].values()):
            raise ValueError("Not all required agents are available")
        
        return context
    
    async def _execute_risk_assessment(self, location: str) -> Dict:
        """Execute data intelligence and risk assessment"""
        self.logger.info(f"Executing risk assessment for {location}")
        
        try:
            # Main outbreak risk analysis
            risk_analysis = await self.data_agent.analyze_outbreak_risk(location)
            
            # Validate rumors if any are detected
            insights = risk_analysis.get("insights", [])
            rumors_to_check = self._extract_potential_rumors(insights)
            
            if rumors_to_check:
                rumor_validation = await self.data_agent.validate_rumors(
                    rumors_to_check, location
                )
                risk_analysis["rumor_validation"] = rumor_validation
            
            return risk_analysis
            
        except Exception as e:
            self.logger.error(f"Risk assessment failed: {str(e)}")
            # Return minimal risk analysis to allow workflow to continue
            return {
                "location": location,
                "risk_score": 25.0,
                "risk_level": "MODERATE",
                "confidence": 0.5,
                "error": str(e),
                "insights": ["Risk assessment failed - using default moderate risk level"]
            }
    
    async def _generate_public_guidance(self, risk_analysis: Dict, location: str,
                                      target_audience: str) -> Dict:
        """Generate public health guidance"""
        self.logger.info(f"Generating public guidance for {location}")
        
        try:
            guidance = await self.guidance_agent.generate_public_guidance(
                risk_analysis, location, target_audience
            )
            return guidance
            
        except Exception as e:
            self.logger.error(f"Guidance generation failed: {str(e)}")
            # Return basic guidance to allow workflow to continue
            risk_level = risk_analysis.get("risk_level", "MODERATE")
            return {
                "location": location,
                "target_audience": target_audience,
                "risk_level": risk_level,
                "key_recommendations": [
                    "Follow local health department guidance",
                    "Monitor official health communications",
                    "Contact healthcare providers with questions"
                ],
                "error": str(e)
            }
    
    async def _generate_resource_report(self, risk_analysis: Dict, location: str,
                                      generate_pdf: bool) -> Dict:
        """Generate resource allocation report"""
        self.logger.info(f"Generating resource report for {location}")
        
        try:
            resource_report = await self.resource_agent.generate_resource_report(
                risk_analysis, location
            )
            return resource_report
            
        except Exception as e:
            self.logger.error(f"Resource report generation failed: {str(e)}")
            # Return minimal resource assessment
            return {
                "location": location,
                "risk_context": risk_analysis,
                "status": "UNABLE_TO_ASSESS",
                "recommendations": ["Contact local emergency management"],
                "error": str(e)
            }
    
    async def _compile_final_report(self, workflow_id: str, risk_analysis: Dict,
                                  guidance: Dict, resource_report: Dict) -> Dict:
        """Compile all agent outputs into unified report"""
        self.logger.info(f"Compiling final report for workflow {workflow_id}")
        
        final_report = {
            "workflow_id": workflow_id,
            "generation_timestamp": datetime.now().isoformat(),
            "location": risk_analysis.get("location"),
            "phoenix_intelligence_summary": self._create_intelligence_summary(
                risk_analysis, guidance, resource_report
            ),
            "components": {
                "risk_assessment": risk_analysis,
                "public_guidance": guidance,
                "resource_allocation": resource_report
            },
            "executive_dashboard": self._create_executive_dashboard(
                risk_analysis, guidance, resource_report
            ),
            "next_steps": self._generate_next_steps(risk_analysis),
            "validity_period": "7 days",
            "contact_information": self._get_emergency_contacts(
                risk_analysis.get("location", "")
            )
        }
        
        return final_report
    
    def _create_intelligence_summary(self, risk_analysis: Dict, guidance: Dict,
                                   resource_report: Dict) -> Dict:
        """Create high-level intelligence summary"""
        risk_score = risk_analysis.get("risk_score", 0)
        risk_level = risk_analysis.get("risk_level", "UNKNOWN")
        
        # Determine overall threat level
        if risk_level == "CRITICAL":
            threat_level = "IMMEDIATE ACTION REQUIRED"
            threat_color = "🔴"
        elif risk_level == "HIGH":
            threat_level = "ENHANCED RESPONSE NEEDED"
            threat_color = "🟠"
        elif risk_level == "MODERATE":
            threat_level = "INCREASED VIGILANCE"
            threat_color = "🟡"
        else:
            threat_level = "ROUTINE MONITORING"
            threat_color = "🟢"
        
        summary = {
            "threat_level": f"{threat_color} {threat_level}",
            "risk_score": f"{risk_score}/100",
            "location": risk_analysis.get("location"),
            "key_findings": self._extract_key_findings(risk_analysis, guidance, resource_report),
            "critical_actions": self._extract_critical_actions(guidance, resource_report),
            "confidence": risk_analysis.get("confidence", 0.5)
        }
        
        return summary
    
    def _create_executive_dashboard(self, risk_analysis: Dict, guidance: Dict,
                                  resource_report: Dict) -> Dict:
        """Create executive dashboard view"""
        dashboard = {
            "risk_indicators": {
                "overall_risk": risk_analysis.get("risk_score", 0),
                "case_trends": self._extract_trend_indicator(risk_analysis, "cases"),
                "hospital_capacity": self._extract_capacity_indicator(resource_report),
                "public_readiness": self._assess_public_readiness(guidance)
            },
            "key_metrics": {
                "confidence_level": f"{risk_analysis.get('confidence', 0.5) * 100:.0f}%",
                "data_freshness": "Real-time",
                "coverage_area": risk_analysis.get("location", "Unknown")
            },
            "action_items": self._create_action_items(guidance, resource_report),
            "timeline": self._create_response_timeline(risk_analysis)
        }
        
        return dashboard
    
    def _extract_key_findings(self, risk_analysis: Dict, guidance: Dict,
                            resource_report: Dict) -> List[str]:
        """Extract key findings from all analyses"""
        findings = []
        
        # Risk analysis findings
        risk_level = risk_analysis.get("risk_level", "UNKNOWN")
        findings.append(f"Outbreak risk level: {risk_level}")
        
        # Add specific insights
        insights = risk_analysis.get("insights", [])
        findings.extend(insights[:2])  # Top 2 insights
        
        # Resource findings
        if "resource_projections" in resource_report:
            critical_shortages = []
            for resource, projection in resource_report["resource_projections"].items():
                if projection.get("priority") == "CRITICAL":
                    critical_shortages.append(resource)
            
            if critical_shortages:
                findings.append(f"Critical resource shortages: {', '.join(critical_shortages)}")
        
        return findings[:5]  # Top 5 findings
    
    def _extract_critical_actions(self, guidance: Dict, resource_report: Dict) -> List[str]:
        """Extract critical actions from guidance and resource reports"""
        actions = []
        
        # From guidance
        key_recommendations = guidance.get("key_recommendations", [])
        actions.extend(key_recommendations[:3])  # Top 3 recommendations
        
        # From resource report
        procurement_recs = resource_report.get("procurement_recommendations", [])
        if procurement_recs:
            urgent_procurements = [
                rec for rec in procurement_recs 
                if rec.get("timeline", "").lower().startswith("immediate")
            ]
            for proc in urgent_procurements[:2]:  # Top 2 urgent procurements
                actions.append(f"URGENT: Procure {proc.get('resource', 'resources')}")
        
        return actions[:5]  # Top 5 actions
    
    def _extract_trend_indicator(self, risk_analysis: Dict, trend_type: str) -> str:
        """Extract trend indicator for dashboard"""
        trends = risk_analysis.get("trends", {})
        trend_data = trends.get(trend_type, {})
        
        growth_rate = trend_data.get("growth_rate", 0)
        
        if growth_rate > 0.2:
            return "📈 RAPIDLY INCREASING"
        elif growth_rate > 0.1:
            return "↗️ INCREASING"
        elif growth_rate > -0.1:
            return "➡️ STABLE"
        else:
            return "↘️ DECREASING"
    
    def _extract_capacity_indicator(self, resource_report: Dict) -> str:
        """Extract hospital capacity indicator"""
        projections = resource_report.get("resource_projections", {})
        
        if "icu_beds" in projections:
            utilization = projections["icu_beds"].get("utilization_projected", 0)
            
            if utilization > 0.9:
                return "🔴 CRITICAL STRAIN"
            elif utilization > 0.8:
                return "🟠 HIGH UTILIZATION" 
            elif utilization > 0.7:
                return "🟡 MODERATE LOAD"
            else:
                return "🟢 ADEQUATE CAPACITY"
        
        return "❓ UNKNOWN"
    
    def _assess_public_readiness(self, guidance: Dict) -> str:
        """Assess public readiness based on guidance"""
        risk_level = guidance.get("risk_context", {}).get("risk_level", "LOW")
        
        readiness_map = {
            "CRITICAL": "🔴 EMERGENCY PROTOCOLS",
            "HIGH": "🟠 ENHANCED READINESS",
            "MODERATE": "🟡 STANDARD READINESS",
            "LOW": "🟢 ROUTINE STATUS"
        }
        
        return readiness_map.get(risk_level, "❓ UNKNOWN")
    
    def _create_action_items(self, guidance: Dict, resource_report: Dict) -> List[Dict]:
        """Create prioritized action items"""
        actions = []
        
        # High priority actions from guidance
        if guidance.get("risk_context", {}).get("risk_level") in ["CRITICAL", "HIGH"]:
            actions.append({
                "priority": "HIGH",
                "action": "Activate emergency response protocols",
                "owner": "Emergency Management",
                "timeline": "Immediate"
            })
        
        # Resource-based actions
        procurement_recs = resource_report.get("procurement_recommendations", [])
        for rec in procurement_recs[:3]:  # Top 3 procurement recommendations
            actions.append({
                "priority": "MEDIUM",
                "action": f"Procure {rec.get('resource', 'resources')}",
                "owner": "Procurement Team",
                "timeline": rec.get("timeline", "TBD")
            })
        
        return actions
    
    def _create_response_timeline(self, risk_analysis: Dict) -> Dict:
        """Create response timeline based on risk level"""
        risk_level = risk_analysis.get("risk_level", "LOW")
        
        timelines = {
            "CRITICAL": {
                "immediate": "Activate emergency protocols",
                "24_hours": "Resource mobilization",
                "72_hours": "Full response deployment"
            },
            "HIGH": {
                "immediate": "Enhanced monitoring", 
                "24_hours": "Prepare response teams",
                "1_week": "Resource positioning"
            },
            "MODERATE": {
                "24_hours": "Review response plans",
                "1_week": "Staff training",
                "2_weeks": "Equipment checks"
            },
            "LOW": {
                "1_week": "Routine monitoring",
                "1_month": "Preparedness review"
            }
        }
        
        return timelines.get(risk_level, timelines["MODERATE"])
    
    def _generate_next_steps(self, risk_analysis: Dict) -> List[str]:
        """Generate recommended next steps"""
        risk_level = risk_analysis.get("risk_level", "LOW")
        
        next_steps = [
            "Monitor outbreak intelligence updates",
            "Review and update response plans",
            "Coordinate with partner agencies"
        ]
        
        if risk_level in ["CRITICAL", "HIGH"]:
            next_steps.insert(0, "Activate emergency operations center")
            next_steps.insert(1, "Issue public health alerts")
        
        return next_steps
    
    def _get_emergency_contacts(self, location: str) -> Dict:
        """Get emergency contact information"""
        return {
            "local_health_department": f"{location} Health Department",
            "emergency_management": f"{location} Emergency Management",
            "cdc_eoc": "CDC Emergency Operations Center",
            "phoenix_support": "Phoenix Outbreak Intelligence Support"
        }
    
    def _extract_potential_rumors(self, insights: List[str]) -> List[str]:
        """Extract potential rumors from insights for validation"""
        # Simple keyword-based extraction - would be more sophisticated in reality
        rumors = []
        rumor_keywords = ["rumor", "claim", "report", "social media", "unverified"]
        
        for insight in insights:
            if any(keyword in insight.lower() for keyword in rumor_keywords):
                rumors.append(insight)
        
        return rumors[:3]  # Validate top 3 potential rumors
    
    async def _update_stage(self, workflow_id: str, stage: WorkflowStage):
        """Update workflow stage"""
        if workflow_id in self.workflow_state:
            self.workflow_state[workflow_id]["current_stage"] = stage.value
            self.workflow_state[workflow_id]["stage_timestamp"] = datetime.now().isoformat()
        
        self.logger.info(f"Workflow {workflow_id} entered stage: {stage.value}")
    
    async def _finalize_workflow(self, workflow_id: str, final_report: Dict):
        """Finalize workflow execution"""
        if workflow_id in self.workflow_state:
            self.workflow_state[workflow_id]["status"] = "COMPLETED"
            self.workflow_state[workflow_id]["completion_time"] = datetime.now().isoformat()
        
        # Could trigger additional actions like:
        # - Sending notifications
        # - Archiving reports  
        # - Updating dashboards
        
        self.logger.info(f"Workflow {workflow_id} finalized successfully")
    
    async def _handle_workflow_error(self, workflow_id: str, error: Exception):
        """Handle workflow errors gracefully"""
        if workflow_id in self.workflow_state:
            self.workflow_state[workflow_id]["status"] = "FAILED"
            self.workflow_state[workflow_id]["error"] = str(error)
            self.workflow_state[workflow_id]["error_time"] = datetime.now().isoformat()
        
        self.logger.error(f"Workflow {workflow_id} failed with error: {str(error)}")
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get current workflow status"""
        return self.workflow_state.get(workflow_id)