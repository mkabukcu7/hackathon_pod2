"""
Retention Insights Agent - Provides customer trends and retention analytics
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random


class RetentionInsightsAgent:
    """Agent for customer retention insights and trend analysis"""
    
    def __init__(self):
        """Initialize the Retention Insights Agent"""
        pass
        
    def get_customer_insights(
        self,
        customer_id: str,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get real-time insights about a customer
        
        Args:
            customer_id: Customer ID
            customer_data: Customer profile data
            
        Returns:
            Dictionary containing customer insights
        """
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
            renewal_date = datetime.fromisoformat(policy["renewal_date"])
            days_to_renewal = (renewal_date - datetime.now()).days
            
            if days_to_renewal <= 30:
                insights.append({
                    "category": "renewal",
                    "type": "urgent",
                    "icon": "🔔",
                    "title": f"{policy['type']} Renewal Due Soon",
                    "description": f"Renews in {days_to_renewal} days - Time to engage",
                    "action": "Proactive renewal call with retention offers"
                })
                
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
            "generated_at": datetime.now().isoformat()
        }
        
    def get_customer_trends(
        self,
        customer_id: str,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze customer trends over time
        
        Args:
            customer_id: Customer ID
            customer_data: Customer profile data
            
        Returns:
            Dictionary containing trend analysis
        """
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
        
        return {
            "customer_id": customer_id,
            "customer_name": customer_data.get("name"),
            "retention_score": score,
            "risk_level": "Low" if score >= 80 else "Medium" if score >= 60 else "High",
            "factors": factors,
            "recommendations": self._get_retention_recommendations(score, factors),
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
