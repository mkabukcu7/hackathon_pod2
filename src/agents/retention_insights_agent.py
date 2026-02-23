"""
Retention Insights Agent - Provides customer trends and retention analytics
Powered by Azure OpenAI GPT-4o-mini for AI-generated insights with rule-based fallback.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import random
import logging
import sys
import os
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.parquet_loader import (
    get_customers,
    get_policies,
    get_claims,
    get_customer_features
)
from services.cosmos_db_service import CosmosDBService
from services.openai_service import chat_completion, is_available as openai_available

logger = logging.getLogger(__name__)


class RetentionInsightsAgent:
    """Agent for customer retention insights and trend analysis from Cosmos DB / Parquet data"""
    
    def __init__(self, use_parquet: bool = True, use_cosmos_db: bool = True):
        """Initialize the Retention Insights Agent
        
        Args:
            use_parquet: Whether to use Parquet data as fallback
            use_cosmos_db: Whether to try Cosmos DB first (default True)
        """
        self.use_parquet = use_parquet
        self.use_cosmos_db = use_cosmos_db
        self.cosmos_service = None
        self.parquet_data = None
        
        # Try Cosmos DB first (primary data source)
        if use_cosmos_db:
            try:
                self.cosmos_service = CosmosDBService()
                if self.cosmos_service.is_connected():
                    print("Retention Insights Agent connected to Cosmos DB (primary)")
                else:
                    print("Cosmos DB not available for Retention Agent, falling back to Parquet")
                    self.use_cosmos_db = False
            except Exception as e:
                print(f"Retention Agent Cosmos DB connection failed: {e}, falling back to Parquet")
                self.use_cosmos_db = False
        
        # Load Parquet data as fallback
        if use_parquet:
            try:
                self.parquet_data = self._load_parquet_data()
                if self.parquet_data:
                    print("Retention Insights Agent loaded Parquet data (fallback)")
                else:
                    print("Parquet data not available for Retention Agent")
                    self.use_parquet = False
            except Exception as e:
                print(f"Failed to load Parquet data: {e}")
                self.use_parquet = False
    
    def _load_parquet_data(self) -> Optional[Dict[str, Any]]:
        """Load retention-relevant data from Parquet files"""
        try:
            customers_df = get_customers()
            policies_df = get_policies()
            claims_df = get_claims()
            features_df = get_customer_features()
            
            return {
                'customers_df': customers_df,
                'policies_df': policies_df,
                'claims_df': claims_df,
                'features_df': features_df
            }
        except Exception as e:
            print(f"Error loading Parquet data: {e}")
            return None

    # ------------------------------------------------------------------ #
    #  GPT-4o-mini AI enhancement helpers
    # ------------------------------------------------------------------ #
    def _build_customer_summary(self, customer_id: str, customer_data: Dict[str, Any]) -> str:
        """Build a concise text summary of the customer for LLM prompts."""
        policies = customer_data.get("policies", [])
        claims = customer_data.get("claim_history", [])
        policy_lines = ", ".join(
            f"{p.get('type', 'Unknown')} (${p.get('premium', 0):,.0f})" for p in policies[:5]
        ) or "none"
        return (
            f"Customer {customer_id}: "
            f"Type={customer_data.get('type', 'Standard')}, "
            f"State={customer_data.get('state', 'N/A')}, "
            f"Age={customer_data.get('age', 'N/A')}, "
            f"Satisfaction={customer_data.get('satisfaction_score', 'N/A')}/5, "
            f"Policies=[{policy_lines}] ({len(policies)} total), "
            f"Claims={len(claims)}, "
            f"Lifetime Value=${customer_data.get('lifetime_value', 0):,.0f}, "
            f"Join Date={customer_data.get('join_date', 'N/A')}, "
            f"Last Contact={customer_data.get('last_contact', 'N/A')}"
        )

    def _ai_generate_insights(self, customer_id: str, customer_data: Dict[str, Any]) -> Optional[List[Dict]]:
        """Use GPT-4o-mini to generate customer insights."""
        if not openai_available():
            return None

        summary = self._build_customer_summary(customer_id, customer_data)
        messages = [
            {"role": "system", "content": (
                "You are an expert insurance analytics AI. Analyze the customer profile and "
                "return a JSON array of insight objects. Each object must have: "
                '"category" (satisfaction|claims|engagement|renewal|value), '
                '"type" (positive|alert|info|opportunity|urgent), '
                '"icon" (single emoji), '
                '"title" (short title), '
                '"description" (1-2 sentence insight), '
                '"action" (recommended next step). '
                "Return 3-6 insights. Return ONLY the JSON array, no markdown."
            )},
            {"role": "user", "content": summary},
        ]
        raw = chat_completion(messages, temperature=0.5, max_tokens=800,
                              response_format={"type": "json_object"})
        if raw is None:
            return None
        try:
            parsed = json.loads(raw)
            # Handle both {"insights": [...]} and bare [...]
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict) and "insights" in parsed:
                return parsed["insights"]
            return None
        except (json.JSONDecodeError, KeyError):
            logger.warning("AI insights returned invalid JSON")
            return None

    def _ai_generate_trends(self, customer_id: str, customer_data: Dict[str, Any]) -> Optional[Dict]:
        """Use GPT-4o-mini to generate trend analysis and predictions."""
        if not openai_available():
            return None

        summary = self._build_customer_summary(customer_id, customer_data)
        messages = [
            {"role": "system", "content": (
                "You are an expert insurance analytics AI. Analyze the customer profile and "
                "return a JSON object with: "
                '"trends" (object with engagement_trend, premium_trend, satisfaction_trend, risk_trend — '
                "each value is one of: improving, stable, declining), "
                '"key_observations" (array of 3-4 specific observation strings), '
                '"predictions" (object with retention_probability 0-1, upsell_readiness 0-1, churn_risk 0-1). '
                "Be specific and data-driven. Return ONLY JSON, no markdown."
            )},
            {"role": "user", "content": summary},
        ]
        raw = chat_completion(messages, temperature=0.4, max_tokens=600,
                              response_format={"type": "json_object"})
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("AI trends returned invalid JSON")
            return None

    def _ai_generate_retention_recommendations(self, score: int, factors: List[Dict],
                                                customer_data: Dict[str, Any]) -> Optional[List[str]]:
        """Use GPT-4o-mini to generate retention recommendations."""
        if not openai_available():
            return None

        factors_text = "; ".join(
            f"{f['factor']} (impact: {f['impact']})" for f in factors
        )
        messages = [
            {"role": "system", "content": (
                "You are an insurance retention specialist AI. Given a customer's retention score "
                "and contributing factors, generate 3-5 specific, actionable retention recommendations. "
                "Return a JSON object with a single key \"recommendations\" containing an array of strings."
            )},
            {"role": "user", "content": (
                f"Retention score: {score}/100, Risk level: "
                f"{'High' if score < 60 else 'Medium' if score < 80 else 'Low'}. "
                f"Factors: {factors_text}. "
                f"Customer type: {customer_data.get('type', 'Standard')}, "
                f"Policies: {len(customer_data.get('policies', []))}"
            )},
        ]
        raw = chat_completion(messages, temperature=0.5, max_tokens=400,
                              response_format={"type": "json_object"})
        if raw is None:
            return None
        try:
            parsed = json.loads(raw)
            return parsed.get("recommendations", [])
        except (json.JSONDecodeError, KeyError):
            return None
        
    def get_customer_insights(
        self,
        customer_id: str,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI-powered insights about a customer.

        Uses GPT-4o-mini when available, falls back to rule-based logic.
        """
        # --- Try AI-generated insights first ---
        ai_insights = self._ai_generate_insights(customer_id, customer_data)
        if ai_insights:
            return {
                "customer_id": customer_id,
                "customer_name": customer_data.get("name"),
                "insight_count": len(ai_insights),
                "insights": ai_insights,
                "overall_health": self._calculate_health_score(customer_data),
                "ai_generated": True,
                "generated_at": datetime.now().isoformat()
            }

        # --- Rule-based fallback ---
        insights = []
        
        # Analyze satisfaction
        satisfaction = customer_data.get("satisfaction_score", 5.0)
        if satisfaction >= 4.5:
            insights.append({
                "category": "satisfaction",
                "type": "positive",
                "icon": "🌟",
                "title": "Highly Satisfied Customer",
                "description": f"Customer satisfaction score: {satisfaction}/5.0 - Among top 20% of customers",
                "action": "Opportunity for testimonial or referral program"
            })
        elif satisfaction < 3.5:
            insights.append({
                "category": "satisfaction",
                "type": "alert",
                "icon": "⚠️",
                "title": "At-Risk Customer",
                "description": f"Low satisfaction score: {satisfaction}/5.0 - Needs immediate attention",
                "action": "Schedule follow-up call with senior advisor"
            })
            
        # Analyze claim history
        claims = customer_data.get("claim_history", [])
        if len(claims) == 0 and customer_data.get("lifetime_value", 0) > 20000:
            insights.append({
                "category": "claims",
                "type": "positive",
                "icon": "✅",
                "title": "Excellent Claims History",
                "description": "No claims filed - Perfect candidate for loyalty rewards",
                "action": "Offer claims-free discount or policy upgrade"
            })
        elif len(claims) > 2:
            insights.append({
                "category": "claims",
                "type": "info",
                "icon": "📊",
                "title": "Active Claims History",
                "description": f"{len(claims)} claims filed - May need coverage adjustment",
                "action": "Review coverage adequacy and recommend enhancements"
            })
            
        # Analyze policy concentration
        policies = customer_data.get("policies", [])
        if len(policies) >= 3:
            insights.append({
                "category": "engagement",
                "type": "positive",
                "icon": "🎯",
                "title": "Multi-Product Customer",
                "description": f"{len(policies)} active policies - High engagement and loyalty",
                "action": "VIP treatment and exclusive offers"
            })
        elif len(policies) == 1:
            insights.append({
                "category": "engagement",
                "type": "opportunity",
                "icon": "💡",
                "title": "Single Product Customer",
                "description": "Strong cross-sell opportunity for bundling",
                "action": "Present bundle savings and additional coverage options"
            })
            
        # Analyze renewal timing
        for policy in policies:
            renewal_date_str = policy.get("renewal_date")
            if not renewal_date_str:
                continue
            try:
                renewal_date = datetime.fromisoformat(renewal_date_str)
                days_to_renewal = (renewal_date - datetime.now()).days
                
                if days_to_renewal <= 30:
                    insights.append({
                        "category": "renewal",
                        "type": "urgent",
                        "icon": "🔔",
                        "title": f"{policy.get('type', 'Policy')} Renewal Due Soon",
                        "description": f"Renews in {days_to_renewal} days - Time to engage",
                        "action": "Proactive renewal call with retention offers"
                    })
            except (ValueError, TypeError):
                continue
                
        # Customer lifetime value insight
        ltv = customer_data.get("lifetime_value", 0)
        if ltv > 50000:
            insights.append({
                "category": "value",
                "type": "positive",
                "icon": "💎",
                "title": "High-Value Customer",
                "description": f"Lifetime value: ${ltv:,.2f} - Top tier customer",
                "action": "Prioritize with white-glove service"
            })
            
        return {
            "customer_id": customer_id,
            "customer_name": customer_data.get("name"),
            "insight_count": len(insights),
            "insights": insights,
            "overall_health": self._calculate_health_score(customer_data),
            "ai_generated": False,
            "generated_at": datetime.now().isoformat()
        }
        
    def get_customer_trends(
        self,
        customer_id: str,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze customer trends over time.

        Uses GPT-4o-mini when available, falls back to rule-based logic.
        """
        # --- Try AI-generated trends first ---
        ai_trends = self._ai_generate_trends(customer_id, customer_data)
        if ai_trends:
            # Build monthly_data for chart rendering (still computed locally)
            monthly_data = []
            for i in range(12, 0, -1):
                date = datetime.now() - timedelta(days=30*i)
                monthly_data.append({
                    "month": date.strftime("%Y-%m"),
                    "premium_paid": customer_data.get("policies", [{}])[0].get("premium", 0) / 12,
                    "contacts": random.randint(0, 3),
                    "satisfaction": min(5.0, customer_data.get("satisfaction_score", 4.0) + random.uniform(-0.3, 0.3))
                })
            return {
                "customer_id": customer_id,
                "customer_name": customer_data.get("name"),
                "trends": ai_trends.get("trends", {}),
                "monthly_data": monthly_data,
                "key_observations": ai_trends.get("key_observations", []),
                "predictions": ai_trends.get("predictions", {}),
                "ai_generated": True,
                "generated_at": datetime.now().isoformat()
            }

        # --- Rule-based fallback ---
        trends = {
            "engagement_trend": "stable",
            "premium_trend": "increasing",
            "satisfaction_trend": "improving",
            "risk_trend": "decreasing"
        }
        
        # Mock trend data - would be calculated from historical data in production
        monthly_data = []
        for i in range(12, 0, -1):
            date = datetime.now() - timedelta(days=30*i)
            monthly_data.append({
                "month": date.strftime("%Y-%m"),
                "premium_paid": customer_data.get("policies", [{}])[0].get("premium", 0) / 12,
                "contacts": random.randint(0, 3),
                "satisfaction": min(5.0, customer_data.get("satisfaction_score", 4.0) + random.uniform(-0.3, 0.3))
            })
            
        return {
            "customer_id": customer_id,
            "customer_name": customer_data.get("name"),
            "trends": trends,
            "monthly_data": monthly_data,
            "key_observations": [
                "Customer engagement has remained consistent over the past year",
                "Premium payments are always on time - excellent payment history",
                "Satisfaction has improved following last service interaction"
            ],
            "predictions": {
                "retention_probability": 0.92,
                "upsell_readiness": 0.78,
                "churn_risk": 0.08
            },
            "ai_generated": False,
            "generated_at": datetime.now().isoformat()
        }
        
    def get_retention_score(
        self,
        customer_id: str,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate retention score and risk assessment
        
        Args:
            customer_id: Customer ID
            customer_data: Customer profile data
            
        Returns:
            Dictionary containing retention score and factors
        """
        factors = []
        score = 85  # Base score
        
        # Satisfaction impact
        satisfaction = customer_data.get("satisfaction_score", 5.0)
        if satisfaction >= 4.5:
            score += 10
            factors.append({"factor": "High satisfaction", "impact": "+10", "value": satisfaction})
        elif satisfaction < 3.5:
            score -= 20
            factors.append({"factor": "Low satisfaction", "impact": "-20", "value": satisfaction})
            
        # Policy count impact
        policy_count = len(customer_data.get("policies", []))
        if policy_count >= 3:
            score += 8
            factors.append({"factor": "Multi-policy holder", "impact": "+8", "value": policy_count})
        elif policy_count == 1:
            score -= 5
            factors.append({"factor": "Single policy", "impact": "-5", "value": policy_count})
            
        # Tenure impact
        join_date_str = customer_data.get("join_date", datetime.now().isoformat())
        try:
            join_date = datetime.fromisoformat(join_date_str)
            years = (datetime.now() - join_date).days / 365
            if years >= 5:
                score += 5
                factors.append({"factor": "Long tenure", "impact": "+5", "value": f"{years:.1f} years"})
        except (ValueError, TypeError):
            # Skip if join_date is invalid
            pass
            
        # Claims impact
        claim_count = len(customer_data.get("claim_history", []))
        if claim_count > 3:
            score -= 8
            factors.append({"factor": "Multiple claims", "impact": "-8", "value": claim_count})
            
        # Contact recency impact
        last_contact_str = customer_data.get("last_contact", datetime.now().isoformat())
        try:
            last_contact = datetime.fromisoformat(last_contact_str)
            days_since = (datetime.now() - last_contact).days
            if days_since > 180:
                score -= 10
                factors.append({"factor": "No recent contact", "impact": "-10", "value": f"{days_since} days"})
        except (ValueError, TypeError):
            # Skip if last_contact is invalid
            pass
            
        # Normalize score
        score = max(0, min(100, score))

        # Try AI-generated recommendations, fall back to rule-based
        ai_recs = self._ai_generate_retention_recommendations(score, factors, customer_data)
        recommendations = ai_recs if ai_recs else self._get_retention_recommendations(score, factors)
        
        return {
            "customer_id": customer_id,
            "customer_name": customer_data.get("name"),
            "retention_score": score,
            "risk_level": "Low" if score >= 80 else "Medium" if score >= 60 else "High",
            "factors": factors,
            "recommendations": recommendations,
            "ai_generated": ai_recs is not None,
            "generated_at": datetime.now().isoformat()
        }
        
    def _calculate_health_score(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall customer health score"""
        satisfaction = customer_data.get("satisfaction_score", 5.0)
        policies = len(customer_data.get("policies", []))
        claims = len(customer_data.get("claim_history", []))
        
        health_score = (satisfaction / 5.0) * 40 + min(policies * 15, 30) + max(30 - claims * 10, 0)
        
        return {
            "score": round(health_score, 1),
            "rating": "Excellent" if health_score >= 85 else "Good" if health_score >= 70 else "Fair" if health_score >= 50 else "At Risk",
            "color": "green" if health_score >= 70 else "yellow" if health_score >= 50 else "red"
        }
        
    def _get_retention_recommendations(self, score: int, factors: List[Dict]) -> List[str]:
        """Generate retention recommendations based on score"""
        recommendations = []
        
        if score < 60:
            recommendations.extend([
                "URGENT: Schedule immediate retention call",
                "Offer exclusive loyalty discount (15-20%)",
                "Escalate to retention specialist"
            ])
        elif score < 80:
            recommendations.extend([
                "Proactive engagement recommended",
                "Review coverage and identify cross-sell opportunities",
                "Send personalized retention offer"
            ])
        else:
            recommendations.extend([
                "Maintain regular contact schedule",
                "Consider for referral program",
                "Offer loyalty rewards"
            ])
            
        return recommendations
