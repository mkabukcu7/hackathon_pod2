"""
Sales Intelligence Agent - Provides cross-sell and up-sell recommendations
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random


class SalesIntelligenceAgent:
    """Agent for generating sales recommendations and insights"""
    
    def __init__(self):
        """Initialize the Sales Intelligence Agent"""
        self.product_catalog = self._load_product_catalog()
        
    def get_cross_sell_recommendations(
        self, 
        customer_id: str,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate cross-sell recommendations for a customer
        
        Args:
            customer_id: Customer ID
            customer_data: Customer profile data
            
        Returns:
            Dictionary containing cross-sell recommendations
        """
        current_policies = {p["type"] for p in customer_data.get("policies", [])}
        recommendations = []
        
        # Analyze customer profile and suggest products they don't have
        if "Auto Insurance" in current_policies and "Home Insurance" not in current_policies:
            recommendations.append({
                "product": "Home Insurance",
                "priority": "High",
                "confidence": 0.85,
                "reasoning": "Customer has auto insurance; 78% of auto customers add home insurance",
                "potential_premium": 1650.00,
                "bundle_discount": 15,
                "talking_points": [
                    "We can bundle your auto and home insurance for 15% savings",
                    "Protect your most valuable asset with comprehensive coverage",
                    "Simplified billing with one payment for both policies"
                ]
            })
            
        if len(current_policies) >= 2 and "Life Insurance" not in current_policies:
            recommendations.append({
                "product": "Life Insurance",
                "priority": "High",
                "confidence": 0.75,
                "reasoning": "Multi-policy customer with high lifetime value; good candidate for life insurance",
                "potential_premium": 2800.00,
                "bundle_discount": 10,
                "talking_points": [
                    "As a valued multi-policy customer, you qualify for our preferred life insurance rates",
                    "Protect your family's future with term life coverage",
                    "Additional 10% discount when bundled with existing policies"
                ]
            })
            
        if "Auto Insurance" in current_policies or "Home Insurance" in current_policies:
            recommendations.append({
                "product": "Umbrella Liability Insurance",
                "priority": "Medium",
                "confidence": 0.65,
                "reasoning": "Customer has property insurance; umbrella coverage provides extra protection",
                "potential_premium": 450.00,
                "bundle_discount": 0,
                "talking_points": [
                    "Protect yourself from major liability claims beyond your standard policy limits",
                    "Affordable extra layer of protection for just $450/year",
                    "Peace of mind with $1M to $5M in additional coverage"
                ]
            })
            
        # Add pet insurance for eligible customers
        if customer_data.get("type") == "Premium":
            recommendations.append({
                "product": "Pet Insurance",
                "priority": "Low",
                "confidence": 0.45,
                "reasoning": "Premium customers often have pets; 62% interest rate in this segment",
                "potential_premium": 480.00,
                "bundle_discount": 5,
                "talking_points": [
                    "Many of our premium customers protect their furry family members",
                    "Coverage for accidents, illnesses, and routine care",
                    "5% discount for bundling with existing policies"
                ]
            })
            
        return {
            "customer_id": customer_id,
            "customer_name": customer_data.get("name"),
            "recommendation_count": len(recommendations),
            "recommendations": recommendations,
            "total_potential_revenue": sum(r["potential_premium"] for r in recommendations),
            "generated_at": datetime.now().isoformat()
        }
        
    def get_upsell_recommendations(
        self,
        customer_id: str,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate up-sell recommendations for existing policies
        
        Args:
            customer_id: Customer ID
            customer_data: Customer profile data
            
        Returns:
            Dictionary containing up-sell recommendations
        """
        recommendations = []
        
        for policy in customer_data.get("policies", []):
            coverage = policy.get("coverage", "Standard")
            if coverage == "Standard":
                recommendations.append({
                    "policy_number": policy["policy_number"],
                    "policy_type": policy["type"],
                    "current_coverage": "Standard",
                    "recommended_coverage": "Comprehensive",
                    "priority": "High",
                    "confidence": 0.80,
                    "additional_premium": 350.00,
                    "reasoning": "Customer has good claim history and qualifies for comprehensive coverage",
                    "benefits": [
                        "Lower deductible: $250 vs $500",
                        "Rental car coverage included",
                        "Roadside assistance 24/7",
                        "New car replacement within first 2 years"
                    ],
                    "talking_points": [
                        "Your excellent driving record qualifies you for our best rates",
                        "Upgrade to comprehensive for just $29/month more",
                        "Enhanced protection with lower out-of-pocket costs"
                    ]
                })
            elif policy.get("coverage") == "Comprehensive" and policy["type"] == "Auto Insurance":
                recommendations.append({
                    "policy_number": policy["policy_number"],
                    "policy_type": policy["type"],
                    "current_coverage": "Comprehensive",
                    "recommended_coverage": "Premium Plus with Accident Forgiveness",
                    "priority": "Medium",
                    "confidence": 0.70,
                    "additional_premium": 180.00,
                    "reasoning": "Long-term customer with low claim history; ideal for accident forgiveness",
                    "benefits": [
                        "First accident forgiven - rates won't increase",
                        "Glass repair with no deductible",
                        "Custom parts and equipment coverage",
                        "Premium rental car coverage"
                    ],
                    "talking_points": [
                        "Lock in your current rate even after your first accident",
                        "Perfect for protecting your clean record and avoiding surprises",
                        "Premium benefits for just $15/month more"
                    ]
                })
                
        return {
            "customer_id": customer_id,
            "customer_name": customer_data.get("name"),
            "recommendation_count": len(recommendations),
            "recommendations": recommendations,
            "total_additional_revenue": sum(r["additional_premium"] for r in recommendations),
            "generated_at": datetime.now().isoformat()
        }
        
    def get_retention_offers(
        self,
        customer_id: str,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate retention offers for at-risk customers
        
        Args:
            customer_id: Customer ID
            customer_data: Customer profile data
            
        Returns:
            Dictionary containing retention strategies
        """
        offers = []
        
        # Check if customer is at risk
        satisfaction = customer_data.get("satisfaction_score", 5.0)
        last_contact = datetime.fromisoformat(customer_data.get("last_contact", datetime.now().isoformat()))
        days_since_contact = (datetime.now() - last_contact).days
        
        if satisfaction < 4.0:
            offers.append({
                "type": "satisfaction_recovery",
                "priority": "High",
                "offer": "Personal account review with senior advisor",
                "discount": 0,
                "reasoning": "Low satisfaction score indicates need for personal attention",
                "talking_points": [
                    "We value your business and want to ensure you're completely satisfied",
                    "Complimentary policy review to optimize your coverage and costs",
                    "Direct line to a senior advisor for any concerns"
                ]
            })
            
        if days_since_contact > 180:
            offers.append({
                "type": "engagement_renewal",
                "priority": "Medium",
                "offer": "Loyalty appreciation discount - 10% off next renewal",
                "discount": 10,
                "reasoning": "Long-term customer needs re-engagement",
                "talking_points": [
                    "As a valued long-term customer, we're offering an exclusive 10% loyalty discount",
                    "Let's review your policies to ensure you have the best coverage",
                    "We've added new benefits since we last spoke"
                ]
            })
            
        # Check for upcoming renewals
        for policy in customer_data.get("policies", []):
            renewal_date_str = policy.get("renewal_date")
            if not renewal_date_str:
                continue  # Skip policies without renewal date
                
            try:
                renewal_date = datetime.fromisoformat(renewal_date_str)
                days_to_renewal = (renewal_date - datetime.now()).days
                
                if 30 <= days_to_renewal <= 60:
                    offers.append({
                        "type": "early_renewal_incentive",
                        "priority": "Medium",
                        "offer": f"Early renewal bonus for {policy['type']}",
                        "discount": 5,
                        "reasoning": f"Policy {policy['policy_number']} renews in {days_to_renewal} days",
                        "talking_points": [
                            f"Renew your {policy['type']} early and save 5%",
                            "Lock in current rates before any market increases",
                            "Simplified renewal process - done in minutes"
                        ]
                    })
            except (ValueError, TypeError):
                # Skip policies with invalid renewal dates
                continue
                
        return {
            "customer_id": customer_id,
            "customer_name": customer_data.get("name"),
            "retention_risk": "High" if satisfaction < 4.0 or days_since_contact > 180 else "Low",
            "offer_count": len(offers),
            "offers": offers,
            "generated_at": datetime.now().isoformat()
        }
        
    def generate_talking_points(
        self,
        customer_id: str,
        customer_data: Dict[str, Any],
        context: str = "general"
    ) -> Dict[str, Any]:
        """Generate AI-powered talking points for customer interaction
        
        Args:
            customer_id: Customer ID
            customer_data: Customer profile data
            context: Context for talking points (general, sales, retention, service)
            
        Returns:
            Dictionary containing talking points and conversation starters
        """
        talking_points = {
            "greeting": f"Hello {customer_data.get('name', 'valued customer')}! It's great to connect with you today.",
            "relationship_highlights": [],
            "conversation_starters": [],
            "key_facts": [],
            "closing": "Is there anything else I can help you with today?"
        }
        
        # Add relationship highlights
        join_date_str = customer_data.get("join_date", datetime.now().isoformat())
        try:
            years_with_company = (datetime.now() - datetime.fromisoformat(join_date_str)).days / 365
            talking_points["relationship_highlights"].append(
                f"You've been with us for {years_with_company:.1f} years - thank you for your loyalty!"
            )
        except (ValueError, TypeError):
            # Skip if join_date is invalid
            pass
        
        if customer_data.get("type") == "Premium":
            talking_points["relationship_highlights"].append(
                "As a Premium customer, you have access to our best rates and exclusive benefits"
            )
            
        # Add conversation starters based on context
        if context == "sales":
            talking_points["conversation_starters"].extend([
                "I noticed you might benefit from bundling opportunities that could save you money",
                "Have you thought about enhancing your coverage to better protect your assets?",
                "We have some new products that align perfectly with your current policies"
            ])
        elif context == "retention":
            talking_points["conversation_starters"].extend([
                "I wanted to personally check in and make sure you're satisfied with your coverage",
                "We have some exclusive offers available for valued customers like yourself",
                "Let's review your policies to ensure they still meet your needs"
            ])
        else:
            talking_points["conversation_starters"].extend([
                "How can I assist you today?",
                "I'd be happy to review your account and answer any questions",
                "Is there anything about your coverage you'd like to discuss?"
            ])
            
        # Add key facts
        talking_points["key_facts"].extend([
            f"Total policies: {len(customer_data.get('policies', []))}",
            f"Customer type: {customer_data.get('type')}",
            f"Satisfaction score: {customer_data.get('satisfaction_score')}/5.0",
            f"Claims filed: {len(customer_data.get('claim_history', []))}"
        ])
        
        return {
            "customer_id": customer_id,
            "context": context,
            "talking_points": talking_points,
            "generated_at": datetime.now().isoformat()
        }
        
    def _load_product_catalog(self) -> Dict[str, Any]:
        """Load product catalog (mock implementation)"""
        return {
            "auto": {"name": "Auto Insurance", "base_premium": 1000},
            "home": {"name": "Home Insurance", "base_premium": 1500},
            "life": {"name": "Life Insurance", "base_premium": 2500},
            "umbrella": {"name": "Umbrella Liability", "base_premium": 400},
            "pet": {"name": "Pet Insurance", "base_premium": 450}
        }
