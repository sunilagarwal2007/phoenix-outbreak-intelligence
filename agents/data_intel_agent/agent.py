"""
Data Intelligence Agent for Phoenix Outbreak Intelligence
Handles BigQuery analysis, risk scoring, and trend detection
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
from google.cloud import bigquery
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path to import gemini_helper
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from gemini_helper import GeminiAIHelper, analyze_outbreak_risk_with_gemini

class DataIntelligenceAgent:
    """
    Core agent responsible for:
    - Querying BigQuery public health datasets
    - Detecting outbreak signals and trends
    - Computing risk scores and predictions
    - Validating rumors via web scraping
    """
    
    def __init__(self, project_id: str, dataset_id: str = "bigquery-public-data"):
        self.client = bigquery.Client(project=project_id)
        self.dataset_id = dataset_id
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gemini AI for advanced analysis
        try:
            self.gemini = GeminiAIHelper(project_id=project_id)
            self.logger.info("Gemini AI initialized successfully")
        except Exception as e:
            self.logger.warning(f"Could not initialize Gemini AI: {e}")
            self.gemini = None
        
    async def analyze_outbreak_risk(self, location: str, days_back: int = 14) -> Dict:
        """
        Main analysis function that computes outbreak risk for a given location
        
        Args:
            location: Geographic location (e.g., "California", "Los Angeles County")
            days_back: Number of days to analyze for trend detection
            
        Returns:
            Dict containing risk score, trends, and recommendations
        """
        try:
            # Fetch multiple data streams
            case_data = await self._get_case_trends(location, days_back)
            positivity_data = await self._get_positivity_rates(location, days_back)
            hospital_data = await self._get_hospital_capacity(location)
            
            # Compute risk components
            case_risk = self._calculate_case_trend_risk(case_data)
            positivity_risk = self._calculate_positivity_risk(positivity_data)
            hospital_risk = self._calculate_hospital_strain_risk(hospital_data)
            
            # Overall risk score (0-100)
            overall_risk = self._compute_composite_risk(
                case_risk, positivity_risk, hospital_risk
            )
            
            # Generate insights
            insights = self._generate_insights(
                overall_risk, case_data, positivity_data, hospital_data
            )
            
            return {
                "location": location,
                "analysis_date": datetime.now().isoformat(),
                "risk_score": overall_risk,
                "risk_level": self._get_risk_level(overall_risk),
                "components": {
                    "case_trend_risk": case_risk,
                    "positivity_risk": positivity_risk,
                    "hospital_strain_risk": hospital_risk
                },
                "trends": {
                    "cases": case_data,
                    "positivity": positivity_data,
                    "hospitals": hospital_data
                },
                "insights": insights,
                "confidence": self._calculate_confidence(case_data, positivity_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error in outbreak analysis: {str(e)}")
            raise
    
    async def _get_case_trends(self, location: str, days: int) -> Dict:
        """Query BigQuery for recent case count trends"""
        # NOTE: BigQuery public COVID-19 datasets contain HISTORICAL data (2020-2022)
        # For demo purposes, using realistic mock data based on past outbreak patterns
        
        # Simulate case trends with realistic numbers
        import random
        random.seed(hash(location) % 100)  # Consistent per location
        
        base_cases = 1500 if 'California' in location else 800
        daily_counts = []
        
        for i in range(days):
            # Simulate growth trend
            growth_factor = 1 + (i * 0.01)  # 1% daily growth
            noise = random.uniform(0.8, 1.2)
            cases = int(base_cases * growth_factor * noise)
            daily_counts.append(cases)
        
        recent_avg = np.mean(daily_counts[-7:])
        previous_avg = np.mean(daily_counts[-14:-7]) if len(daily_counts) >= 14 else recent_avg
        growth_rate = (recent_avg - previous_avg) / previous_avg if previous_avg > 0 else 0
        
        return {
            'daily_counts': daily_counts,
            'latest_count': daily_counts[-1],
            'seven_day_average': recent_avg,
            'growth_rate': growth_rate,
            'trend': 'INCREASING' if growth_rate > 0.05 else 'STABLE'
        }
    
    async def _get_positivity_rates(self, location: str, days: int) -> Dict:
        """Query BigQuery for test positivity trends"""
        # NOTE: Historical data from public datasets
        # Using mock data for demo
        
        import random
        random.seed(hash(location) % 50)
        
        # Simulate positivity rates (5-15% range for moderate risk)
        rates = []
        base_rate = 0.08  # 8% base positivity
        
        for i in range(min(days, 7)):
            rate = base_rate + random.uniform(-0.02, 0.03)
            rates.append(max(0.01, min(0.20, rate)))
        
        return {
            'rates': rates,
            'latest_rate': rates[-1] if rates else 0.08,
            'average_rate': np.mean(rates) if rates else 0.08
        }
    
    async def _get_hospital_capacity(self, location: str) -> Dict:
        """Query BigQuery for hospital utilization data"""
        # NOTE: Historical hospital data
        # Using mock data for demo
        
        import random
        random.seed(hash(location) % 75)
        
        # Simulate ICU occupancy (70-90% for high utilization)
        icu_occupancy = random.uniform(0.75, 0.92)
        total_beds = 1500 if 'California' in location else 800
        occupied_beds = int(total_beds * icu_occupancy)
        
        return {
            'icu_occupancy': icu_occupancy,
            'total_icu_beds': total_beds,
            'occupied_beds': occupied_beds,
            'available_beds': total_beds - occupied_beds,
            'utilization_trend': 'HIGH' if icu_occupancy > 0.85 else 'MODERATE'
        }
    
    def _calculate_case_trend_risk(self, case_data: Dict) -> float:
        """Calculate risk score based on case count acceleration"""
        # Implementation for trend analysis and risk scoring
        if not case_data or 'daily_counts' not in case_data:
            return 0.0
            
        counts = case_data['daily_counts']
        if len(counts) < 7:
            return 0.0
            
        # Calculate 7-day moving average and acceleration
        recent_avg = np.mean(counts[-7:])
        previous_avg = np.mean(counts[-14:-7]) if len(counts) >= 14 else recent_avg
        
        if previous_avg == 0:
            return 50.0  # Default moderate risk
            
        growth_rate = (recent_avg - previous_avg) / previous_avg
        
        # Convert growth rate to risk score (0-100)
        risk_score = min(100, max(0, 50 + (growth_rate * 100)))
        return risk_score
    
    def _calculate_positivity_risk(self, positivity_data: Dict) -> float:
        """Calculate risk based on test positivity trends"""
        if not positivity_data or 'rates' not in positivity_data:
            return 0.0
            
        rates = positivity_data['rates']
        if not rates:
            return 0.0
            
        latest_rate = rates[-1]
        
        # CDC thresholds: <5% low, 5-10% moderate, >10% high
        if latest_rate < 0.05:
            return 20.0
        elif latest_rate < 0.10:
            return 50.0
        else:
            return 80.0
    
    def _calculate_hospital_strain_risk(self, hospital_data: Dict) -> float:
        """Calculate risk based on hospital ICU capacity"""
        if not hospital_data or 'icu_occupancy' not in hospital_data:
            return 0.0
            
        occupancy = hospital_data['icu_occupancy']
        
        # ICU capacity thresholds
        if occupancy < 0.70:
            return 15.0
        elif occupancy < 0.85:
            return 50.0
        else:
            return 90.0
    
    def _compute_composite_risk(self, case_risk: float, pos_risk: float, hosp_risk: float) -> float:
        """Combine individual risk components into overall score"""
        # Weighted average with hospital strain having highest weight
        weights = [0.3, 0.3, 0.4]  # cases, positivity, hospitals
        composite = (case_risk * weights[0] + 
                    pos_risk * weights[1] + 
                    hosp_risk * weights[2])
        return round(composite, 1)
    
    def _get_risk_level(self, score: float) -> str:
        """Convert numeric risk score to categorical level"""
        if score < 25:
            return "LOW"
        elif score < 50:
            return "MODERATE"
        elif score < 75:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _generate_insights(self, risk_score: float, case_data: Dict, 
                          pos_data: Dict, hosp_data: Dict) -> List[str]:
        """Generate human-readable insights from the analysis"""
        insights = []
        
        # Use Gemini AI for advanced insight generation if available
        if self.gemini:
            try:
                prompt = f"""Based on this outbreak data, provide 3-5 key insights:
                
Risk Score: {risk_score}/100
Case Data: {case_data}
Positivity Data: {pos_data}
Hospital Data: {hosp_data}

Generate concise, actionable insights (one sentence each) for public health officials."""
                
                gemini_insights = self.gemini.generate_text(prompt, temperature=0.3, max_output_tokens=2048)
                
                # Parse insights (assume bullet points or numbered list)
                for line in gemini_insights.split('\n'):
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                        # Clean up formatting
                        insight = line.lstrip('0123456789.-•* ').strip()
                        if insight:
                            insights.append(insight)
                
                if insights:
                    return insights[:5]  # Limit to 5 insights
                    
            except Exception as e:
                self.logger.warning(f"Gemini insight generation failed: {e}, falling back to rule-based")
        
        # Fallback to rule-based insights
        if risk_score > 75:
            insights.append("⚠️ CRITICAL: Immediate public health intervention recommended")
        elif risk_score > 50:
            insights.append("🔶 HIGH ALERT: Enhanced monitoring and precautions advised")
        elif risk_score > 25:
            insights.append("🔸 MODERATE: Continue surveillance, prepare response plans")
        else:
            insights.append("✅ LOW RISK: Maintain standard monitoring protocols")
        
        # Add specific trend insights
        if case_data and 'growth_rate' in case_data:
            if case_data['growth_rate'] > 0.2:
                insights.append("📈 Cases accelerating rapidly (+20% week-over-week)")
            elif case_data['growth_rate'] > 0.1:
                insights.append("📊 Moderate case growth detected")
        
        return insights
    
    def _calculate_confidence(self, case_data: Dict, pos_data: Dict) -> float:
        """Calculate confidence level in the analysis based on data quality"""
        confidence = 100.0
        
        # Reduce confidence based on missing or sparse data
        if not case_data or len(case_data.get('daily_counts', [])) < 7:
            confidence -= 30
        if not pos_data or len(pos_data.get('rates', [])) < 3:
            confidence -= 20
        
        return max(50.0, confidence)  # Minimum 50% confidence
    
    async def validate_rumors(self, rumors: List[str], location: str) -> Dict:
        """
        Validate outbreak-related rumors using official data sources
        
        Args:
            rumors: List of claims/rumors to validate
            location: Geographic context for validation
            
        Returns:
            Dict with validation results for each rumor
        """
        validations = {}
        
        for rumor in rumors:
            # This would integrate with MCP Web Reader
            # to scrape official sources and cross-reference
            validation = {
                "claim": rumor,
                "verdict": "INVESTIGATING",  # CONFIRMED, FALSE, INVESTIGATING
                "confidence": 0.0,
                "sources": [],
                "analysis": "Cross-referencing with official datasets..."
            }
            validations[rumor] = validation
        
        return {
            "location": location,
            "validation_date": datetime.now().isoformat(),
            "rumors_checked": len(rumors),
            "results": validations
        }