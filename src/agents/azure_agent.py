"""
Azure Agent - Integrates with Azure services for resource management and monitoring
"""
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.openai_service import chat_completion, is_available as openai_available


class AzureAgent:
    """Agent for Azure service integration"""
    
    def __init__(
        self, 
        subscription_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        """Initialize the Azure Agent
        
        Args:
            subscription_id: Azure subscription ID (optional, defaults to env variable)
            tenant_id: Azure tenant ID (optional, defaults to env variable)
            client_id: Azure client ID (optional, defaults to env variable)
            client_secret: Azure client secret (optional, defaults to env variable)
        """
        self.subscription_id = subscription_id or os.getenv("AZURE_SUBSCRIPTION_ID")
        self.tenant_id = tenant_id or os.getenv("AZURE_TENANT_ID")
        self.client_id = client_id or os.getenv("AZURE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("AZURE_CLIENT_SECRET")
        self.credential = None
        
        # Initialize Azure clients if credentials are available
        if all([self.subscription_id, self.tenant_id, self.client_id, self.client_secret]):
            try:
                from azure.identity import ClientSecretCredential
                self.credential = ClientSecretCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
            except ImportError:
                pass  # Azure SDK not installed
                
    def get_resource_groups(self) -> Dict[str, Any]:
        """Get list of resource groups in the subscription
        
        Returns:
            Dictionary containing resource group information
        """
        if not self.credential or not self.subscription_id:
            return {
                "error": "Azure credentials not configured",
                "resource_groups": []
            }
            
        try:
            from azure.mgmt.resource import ResourceManagementClient
            
            client = ResourceManagementClient(self.credential, self.subscription_id)
            resource_groups = []
            
            for rg in client.resource_groups.list():
                resource_groups.append({
                    "name": rg.name,
                    "location": rg.location,
                    "tags": rg.tags or {}
                })
            
            return {
                "subscription_id": self.subscription_id,
                "resource_group_count": len(resource_groups),
                "resource_groups": resource_groups,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to retrieve resource groups: {str(e)}",
                "resource_groups": []
            }
            
    def get_resources_in_group(self, resource_group: str) -> Dict[str, Any]:
        """Get resources in a specific resource group
        
        Args:
            resource_group: Name of the resource group
            
        Returns:
            Dictionary containing resource information
        """
        if not self.credential or not self.subscription_id:
            return {
                "error": "Azure credentials not configured",
                "resources": []
            }
            
        try:
            from azure.mgmt.resource import ResourceManagementClient
            
            client = ResourceManagementClient(self.credential, self.subscription_id)
            resources = []
            
            for resource in client.resources.list_by_resource_group(resource_group):
                resources.append({
                    "name": resource.name,
                    "type": resource.type,
                    "location": resource.location,
                    "tags": resource.tags or {}
                })
            
            return {
                "resource_group": resource_group,
                "resource_count": len(resources),
                "resources": resources,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to retrieve resources: {str(e)}",
                "resources": []
            }
            
    def get_resource_metrics(
        self, 
        resource_id: str, 
        metric_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get metrics for a specific Azure resource
        
        Args:
            resource_id: Full Azure resource ID
            metric_names: List of metric names to retrieve (optional)
            
        Returns:
            Dictionary containing resource metrics
        """
        if not self.credential:
            return {
                "error": "Azure credentials not configured",
                "metrics": []
            }
            
        # Mock implementation - replace with actual Azure Monitor API call
        return {
            "resource_id": resource_id,
            "metrics": [
                {
                    "name": "CPU Percentage",
                    "value": 45.2,
                    "unit": "Percent",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "name": "Memory Percentage",
                    "value": 62.8,
                    "unit": "Percent",
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    def get_cost_analysis(
        self, 
        resource_group: Optional[str] = None,
        time_period: str = "month"
    ) -> Dict[str, Any]:
        """Get cost analysis for subscription or resource group
        
        Args:
            resource_group: Resource group name (optional, analyzes entire subscription if not provided)
            time_period: Time period for analysis (day, week, month, year)
            
        Returns:
            Dictionary containing cost analysis data
        """
        # Mock implementation - replace with actual Azure Cost Management API call
        result = {
            "scope": resource_group or "subscription",
            "time_period": time_period,
            "total_cost": 1245.67,
            "currency": "USD",
            "cost_by_service": {
                "Virtual Machines": 456.78,
                "Storage": 234.56,
                "Networking": 123.45,
                "Databases": 345.67,
                "Other": 85.21
            },
            "cost_trend": "increasing",
            "forecast": {
                "next_month": 1350.00,
                "confidence": 0.85
            },
            "timestamp": datetime.now().isoformat()
        }

        # Enrich with AI cost optimization analysis
        ai_analysis = self._ai_cloud_analysis(result, "cost")
        if ai_analysis:
            result["ai_cost_analysis"] = ai_analysis
            result["ai_generated"] = True
        else:
            result["ai_generated"] = False

        return result
        
    def get_service_health(self) -> Dict[str, Any]:
        """Get Azure service health status
        
        Returns:
            Dictionary containing service health information
        """
        # Mock implementation - replace with actual Azure Service Health API call
        return {
            "subscription_id": self.subscription_id,
            "overall_status": "Healthy",
            "services": [
                {
                    "name": "Virtual Machines",
                    "status": "Available",
                    "region": "East US"
                },
                {
                    "name": "Storage",
                    "status": "Available",
                    "region": "East US"
                },
                {
                    "name": "App Service",
                    "status": "Degraded",
                    "region": "West Europe",
                    "message": "Investigating connectivity issues"
                }
            ],
            "active_incidents": 1,
            "planned_maintenance": 0,
            "timestamp": datetime.now().isoformat()
        }
        
    def get_security_recommendations(self, resource_group: Optional[str] = None) -> Dict[str, Any]:
        """Get security recommendations from Azure Security Center
        
        Args:
            resource_group: Resource group to scope recommendations (optional)
            
        Returns:
            Dictionary containing security recommendations
        """
        # Mock implementation - replace with actual Azure Security Center API call
        result = {
            "scope": resource_group or "subscription",
            "security_score": 78,
            "recommendations": [
                {
                    "severity": "High",
                    "title": "Enable encryption at rest for storage accounts",
                    "affected_resources": 3,
                    "remediation": "Enable storage account encryption"
                },
                {
                    "severity": "Medium",
                    "title": "Update outdated TLS versions",
                    "affected_resources": 5,
                    "remediation": "Upgrade to TLS 1.2 or higher"
                },
                {
                    "severity": "Low",
                    "title": "Enable diagnostic logs",
                    "affected_resources": 8,
                    "remediation": "Configure diagnostic settings"
                }
            ],
            "timestamp": datetime.now().isoformat()
        }

        # Enrich with AI security analysis
        ai_analysis = self._ai_cloud_analysis(result, "security")
        if ai_analysis:
            result["ai_security_analysis"] = ai_analysis
            result["ai_generated"] = True
        else:
            result["ai_generated"] = False

        return result

    # ---- Azure OpenAI helpers ------------------------------------------------

    def _ai_cloud_analysis(self, data: Dict[str, Any], analysis_type: str) -> Optional[str]:
        """Generate AI-powered cloud infrastructure analysis.

        Args:
            data: The resource/cost/security data dictionary.
            analysis_type: 'cost' or 'security'.

        Returns:
            Analysis string, or None if AI is unavailable.
        """
        if not openai_available():
            return None

        try:
            if analysis_type == "cost":
                cost_breakdown = ", ".join(
                    f"{k}: ${v:,.2f}" for k, v in data.get("cost_by_service", {}).items()
                )
                context = (
                    f"Scope: {data.get('scope')}, Period: {data.get('time_period')}, "
                    f"Total cost: ${data.get('total_cost', 0):,.2f} {data.get('currency', 'USD')}, "
                    f"Cost trend: {data.get('cost_trend')}, "
                    f"Breakdown: {cost_breakdown}, "
                    f"Next month forecast: ${data.get('forecast', {}).get('next_month', 0):,.2f}"
                )
                system_msg = (
                    "You are an Azure FinOps advisor. Given cloud cost data, "
                    "provide a concise 2-3 sentence cost optimization analysis. "
                    "Identify the top cost driver and suggest one specific "
                    "cost-saving action. Do NOT use markdown."
                )
            else:
                recs = "; ".join(
                    f"{r['severity']}: {r['title']} ({r['affected_resources']} resources)"
                    for r in data.get("recommendations", [])
                )
                context = (
                    f"Security score: {data.get('security_score')}/100, "
                    f"Recommendations: {recs}"
                )
                system_msg = (
                    "You are an Azure security advisor. Given security posture data, "
                    "provide a concise 2-3 sentence assessment with the most "
                    "critical action to take first. Do NOT use markdown."
                )

            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": context},
            ]

            return chat_completion(messages, temperature=0.4, max_tokens=200)
        except Exception as e:
            print(f"AI cloud analysis failed: {e}")
            return None
