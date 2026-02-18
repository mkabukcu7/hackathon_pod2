"""
Sales Intelligence Agent - Provides cross-sell and up-sell recommendations
Powered by Azure OpenAI GPT-4o-mini for AI-generated recommendations with rule-based fallback.
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
    get_producer_activity
)
from services.openai_service import chat_completion, is_available as openai_available

logger = logging.getLogger(__name__)


class SalesIntelligenceAgent:
    """Agent for generating sales recommendations and insights from Parquet data"""
    
    def __init__(self, use_parquet: bool = True):
        """Initialize the Sales Intelligence Agent
        
        Args:
            use_parquet: Whether to use Parquet data (True) or mock data (False)
        """
        self.product_catalog = self._load_product_catalog()
        self.use_parquet = use_parquet
        self.parquet_data = None
        
        # Try to load Parquet data
        if use_parquet:
            try:
                self.parquet_data = self._load_parquet_data()
                if self.parquet_data:
                    print("Sales Intelligence Agent loaded Parquet data")
                else:
                    print("Parquet data not available")
                    self.use_parquet = False
            except Exception as e:
                print(f"Failed to load Parquet data: {e}")
                self.use_parquet = False
    
    def _load_parquet_data(self) -> Optional[Dict[str, Any]]:
        """Load sales-relevant data from Parquet files"""
        try:
            customers_df = get_customers()
            policies_df = get_policies()
            activity_df = get_producer_activity()
            
            return {
                'customers_df': customers_df,
                'policies_df': policies_df,
                'activity_df': activity_df
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
        policy_lines = ", ".join(
            f"{p.get('type', 'Unknown')} ({p.get('coverage', 'Standard')}, ${p.get('premium', 0):,.0f})"
            for p in policies[:6]
        ) or "none"
        claims = customer_data.get("claim_history", [])
        return (
            f"Customer {customer_id}: "
            f"Type={customer_data.get('type', 'Standard')}, "
            f"State={customer_data.get('state', 'N/A')}, "
            f"Age={customer_data.get('age', 'N/A')}, "
            f"MaritalStatus={customer_data.get('marital_status', 'N/A')}, "
            f"HasKids={customer_data.get('has_kids', 'N/A')}, "
            f"IsHomeOwner={customer_data.get('is_home_owner', 'N/A')}, "
            f"Satisfaction={customer_data.get('satisfaction_score', 'N/A')}/5, "
            f"CurrentPolicies=[{policy_lines}] ({len(policies)} total), "
            f"Claims={len(claims)}, "
            f"Lifetime Value=${customer_data.get('lifetime_value', 0):,.0f}"
        )

    def _ai_cross_sell(self, customer_id: str, customer_data: Dict[str, Any]) -> Optional[List[Dict]]:
        """Use GPT-4o-mini to generate cross-sell recommendations."""
        if not openai_available():
            return None

        summary = self._build_customer_summary(customer_id, customer_data)
        current_types = [p.get("type", "") for p in customer_data.get("policies", [])]

        messages = [
            {"role": "system", "content": (
                "You are an expert insurance sales analytics AI. "
                "Given a customer profile, recommend insurance products the customer does NOT already have. "
                "Available products: Auto Insurance, Home Insurance, Life Insurance, "
                "Umbrella Liability Insurance, Pet Insurance, Renters Insurance, "
                "Commercial Insurance, Motorcycle Insurance.\n"
                "Return a JSON object with key \"recommendations\" containing an array. "
                "Each item: {\"product\": str, \"priority\": High|Medium|Low, "
                "\"confidence\": 0.0-1.0, \"reasoning\": str, "
                "\"potential_premium\": number, \"bundle_discount\": number 0-20, "
                "\"talking_points\": [str, str, str]}. "
                "Return 2-4 recommendations. Return ONLY JSON."
            )},
            {"role": "user", "content": f"{summary}\nCurrently has: {current_types}"},
        ]
        raw = chat_completion(messages, temperature=0.6, max_tokens=900,
                              response_format={"type": "json_object"})
        if raw is None:
            return None
        try:
            parsed = json.loads(raw)
            recs = parsed.get("recommendations", parsed if isinstance(parsed, list) else [])
            return recs if isinstance(recs, list) else None
        except (json.JSONDecodeError, KeyError):
            logger.warning("AI cross-sell returned invalid JSON")
            return None

    def _ai_upsell(self, customer_id: str, customer_data: Dict[str, Any]) -> Optional[List[Dict]]:
        """Use GPT-4o-mini to generate upsell recommendations."""
        if not openai_available():
            return None

        summary = self._build_customer_summary(customer_id, customer_data)

        messages = [
            {"role": "system", "content": (
                "You are an expert insurance sales analytics AI. "
                "Analyze the customer's existing policies and recommend upgrades/enhancements. "
                "Return a JSON object with key \"recommendations\" containing an array. "
                "Each item: {\"policy_type\": str, \"current_coverage\": str, "
                "\"recommended_coverage\": str, \"priority\": High|Medium|Low, "
                "\"confidence\": 0.0-1.0, \"additional_premium\": number, "
                "\"reasoning\": str, \"benefits\": [str], \"talking_points\": [str]}. "
                "Return 1-3 recommendations. Return ONLY JSON."
            )},
            {"role": "user", "content": summary},
        ]
        raw = chat_completion(messages, temperature=0.6, max_tokens=900,
                              response_format={"type": "json_object"})
        if raw is None:
            return None
        try:
            parsed = json.loads(raw)
            recs = parsed.get("recommendations", parsed if isinstance(parsed, list) else [])
            return recs if isinstance(recs, list) else None
        except (json.JSONDecodeError, KeyError):
            logger.warning("AI upsell returned invalid JSON")
            return None

    def _ai_talking_points(self, customer_id: str, customer_data: Dict[str, Any],
                           context: str) -> Optional[Dict]:
        """Use GPT-4o-mini to generate dynamic talking points."""
        if not openai_available():
            return None

        summary = self._build_customer_summary(customer_id, customer_data)

        messages = [
            {"role": "system", "content": (
                "You are an expert insurance sales coach AI. "
                "Generate personalized talking points for an agent speaking with this customer. "
                f"Conversation context: {context}.\n"
                "Return a JSON object with: "
                "\"greeting\" (personalized greeting), "
                "\"relationship_highlights\" (array of 2-3 strings recognizing the customer's history), "
                "\"conversation_starters\" (array of 3-4 context-appropriate openers), "
                "\"key_facts\" (array of 3-5 data points the agent should know), "
                "\"objection_handlers\" (array of 2-3 anticipated objection responses), "
                "\"closing\" (strong closing statement). "
                "Be warm, professional, and specific to this customer. Return ONLY JSON."
            )},
            {"role": "user", "content": summary},
        ]
        raw = chat_completion(messages, temperature=0.7, max_tokens=900,
                              response_format={"type": "json_object"})
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("AI talking points returned invalid JSON")
            return None
        
    def get_cross_sell_recommendations(
        self, 
        customer_id: str,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate cross-sell recommendations for a customer.

        Uses GPT-4o-mini when available, falls back to rule-based logic.
        """
        # --- Try AI-generated cross-sell first ---
        ai_recs = self._ai_cross_sell(customer_id, customer_data)
        if ai_recs:
            return {
                "customer_id": customer_id,
                "customer_name": customer_data.get("name"),
                "recommendation_count": len(ai_recs),
                "recommendations": ai_recs,
                "total_potential_revenue": sum(
                    r.get("potential_premium", 0) for r in ai_recs
                ),
                "ai_generated": True,
                "generated_at": datetime.now().isoformat()
            }

        # --- Rule-based fallback ---
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
            "ai_generated": False,
            "generated_at": datetime.now().isoformat()
        }
        
    def get_upsell_recommendations(
        self,
        customer_id: str,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate up-sell recommendations for existing policies.

        Uses GPT-4o-mini when available, falls back to rule-based logic.
        """
        # --- Try AI-generated upsell first ---
        ai_recs = self._ai_upsell(customer_id, customer_data)
        if ai_recs:
            return {
                "customer_id": customer_id,
                "customer_name": customer_data.get("name"),
                "recommendation_count": len(ai_recs),
                "recommendations": ai_recs,
                "total_additional_revenue": sum(
                    r.get("additional_premium", 0) for r in ai_recs
                ),
                "ai_generated": True,
                "generated_at": datetime.now().isoformat()
            }

        # --- Rule-based fallback ---
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
            "ai_generated": False,
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
        """Generate AI-powered talking points for customer interaction.

        Uses GPT-4o-mini when available, falls back to rule-based templates.
        """
        # --- Try AI-generated talking points first ---
        ai_tp = self._ai_talking_points(customer_id, customer_data, context)
        if ai_tp:
            return {
                "customer_id": customer_id,
                "context": context,
                "talking_points": ai_tp,
                "ai_generated": True,
                "generated_at": datetime.now().isoformat()
            }

        # --- Rule-based fallback ---
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
            "ai_generated": False,
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
