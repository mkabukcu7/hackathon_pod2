# Azure Resource Setup Guide

This guide provides Azure CLI commands to create all required resources for the hackathon_pod2 application.

## Prerequisites

```bash
# Install Azure CLI if not already installed
# https://learn.microsoft.com/en-us/cli/azure/install-azure-cli

# Login to your Azure account
az login

# Set your subscription (if you have multiple)
az account set --subscription "your-subscription-id"
```

## Environment Variables

Set these before running the commands:

```bash
# Resource configuration
$RESOURCE_GROUP = "hackathon-pod2-rg"
$LOCATION = "eastus"  # Change to your preferred region
$ENVIRONMENT = "dev"  # or "prod"

# Resource names
$MAPS_NAME = "hackathon-maps"
$OPENAI_NAME = "hackathon-openai"
$KEYVAULT_NAME = "hackathon-kv-$(Get-Random -Minimum 1000 -Maximum 9999)"
```

## 1. Create Resource Group

```bash
az group create `
  --name $RESOURCE_GROUP `
  --location $LOCATION
```

## 2. Create Azure Maps Resource

```bash
az maps account create `
  --name $MAPS_NAME `
  --resource-group $RESOURCE_GROUP `
  --sku S0 `
  --kind Gen2

# Get the primary key
$MAPS_KEY = az maps account keys list `
  --name $MAPS_NAME `
  --resource-group $RESOURCE_GROUP `
  --query "primaryKey" `
  --output tsv

Write-Host "AZURE_MAPS_API_KEY=$MAPS_KEY"
```

## 3. Create Azure OpenAI Resource

```bash
# Create the Azure OpenAI resource
az cognitiveservices account create `
  --name $OPENAI_NAME `
  --resource-group $RESOURCE_GROUP `
  --kind OpenAI `
  --sku s0 `
  --location $LOCATION `
  --yes

# Get endpoint
$OPENAI_ENDPOINT = az cognitiveservices account show `
  --name $OPENAI_NAME `
  --resource-group $RESOURCE_GROUP `
  --query "properties.endpoint" `
  --output tsv

# Get API key
$OPENAI_KEY = az cognitiveservices account keys list `
  --name $OPENAI_NAME `
  --resource-group $RESOURCE_GROUP `
  --query "key1" `
  --output tsv

Write-Host "AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT"
Write-Host "AZURE_OPENAI_API_KEY=$OPENAI_KEY"
```

## 4. Deploy OpenAI Model

```bash
# Deploy gpt-35-turbo model (faster, cheaper)
az cognitiveservices account deployment create `
  --name $OPENAI_NAME `
  --resource-group $RESOURCE_GROUP `
  --deployment-name "gpt-35-turbo" `
  --model-name "gpt-35-turbo" `
  --model-version "0613" `
  --sku-capacity 1 `
  --sku-name "Standard"

# Or deploy gpt-4 model (more capable)
az cognitiveservices account deployment create `
  --name $OPENAI_NAME `
  --resource-group $RESOURCE_GROUP `
  --deployment-name "gpt-4" `
  --model-name "gpt-4" `
  --model-version "0613" `
  --sku-capacity 1 `
  --sku-name "Standard"

Write-Host "AZURE_OPENAI_DEPLOYMENT_NAME=gpt-35-turbo"  # or gpt-4
```

## 5. Create Service Principal for Azure Resource Management

```bash
# Create service principal
$SP_OUTPUT = az ad sp create-for-rbac `
  --name "hackathon-pod2-sp" `
  --role "Reader" `
  --scopes "/subscriptions/$((az account show --query id -o tsv))" `
  --output json | ConvertFrom-Json

$CLIENT_ID = $SP_OUTPUT.appId
$CLIENT_SECRET = $SP_OUTPUT.password
$TENANT_ID = $SP_OUTPUT.tenant

Write-Host "AZURE_SUBSCRIPTION_ID=$(az account show --query id -o tsv)"
Write-Host "AZURE_TENANT_ID=$TENANT_ID"
Write-Host "AZURE_CLIENT_ID=$CLIENT_ID"
Write-Host "AZURE_CLIENT_SECRET=$CLIENT_SECRET"
```

## 6. Create Key Vault (Optional but Recommended)

```bash
# Create Key Vault to securely store secrets
az keyvault create `
  --name $KEYVAULT_NAME `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION

# Store Azure Maps key
az keyvault secret set `
  --vault-name $KEYVAULT_NAME `
  --name "AZURE-MAPS-API-KEY" `
  --value $MAPS_KEY

# Store OpenAI key
az keyvault secret set `
  --vault-name $KEYVAULT_NAME `
  --name "AZURE-OPENAI-API-KEY" `
  --value $OPENAI_KEY

# Store service principal secret
az keyvault secret set `
  --vault-name $KEYVAULT_NAME `
  --name "AZURE-CLIENT-SECRET" `
  --value $CLIENT_SECRET

Write-Host "Key Vault created: $KEYVAULT_NAME"
```

## 7. Complete .env Configuration

After running the above commands, update your `.env` file:

```dotenv
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://{your-resource-name}.openai.azure.com/
AZURE_OPENAI_API_KEY={from-step-3}
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-35-turbo
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Azure Resource Management
AZURE_SUBSCRIPTION_ID={from-step-5}
AZURE_TENANT_ID={from-step-5}
AZURE_CLIENT_ID={from-step-5}
AZURE_CLIENT_SECRET={from-step-5}

# Azure Maps Configuration
AZURE_MAPS_API_KEY={from-step-2}

# Application Settings
LOG_LEVEL=INFO
APP_PORT=8000
```

## 8. Verify Resources

```bash
# List all created resources
az resource list `
  --resource-group $RESOURCE_GROUP `
  --output table

# Test Azure Maps API
curl -X GET "https://atlas.microsoft.com/weather/currentConditions/json?query=Seattle&subscription-key=$MAPS_KEY"

# Test Azure OpenAI
curl -X POST "https://{resource-name}.openai.azure.com/openai/deployments/{deployment-id}/chat/completions?api-version=2024-02-15-preview" `
  -H "api-key: $OPENAI_KEY" `
  -H "Content-Type: application/json" `
  -d '{"messages":[{"role":"user","content":"Hello"}]}'
```

## 9. Clean Up (When Done)

```bash
# Delete entire resource group and all resources
az group delete --name $RESOURCE_GROUP --yes

# Or delete individual resources
az maps account delete --name $MAPS_NAME --resource-group $RESOURCE_GROUP
az cognitiveservices account delete --name $OPENAI_NAME --resource-group $RESOURCE_GROUP
az ad sp delete --id $CLIENT_ID
az keyvault delete --name $KEYVAULT_NAME --resource-group $RESOURCE_GROUP
```

## Cost Estimation

| Resource | SKU | Estimated Monthly Cost |
|----------|-----|------------------------|
| Azure Maps | S0 | $50-100 (pay-per-call) |
| Azure OpenAI | gpt-35-turbo | $0.0005/1K tokens |
| Azure OpenAI | gpt-4 | $0.03/1K tokens |
| Service Principal | N/A | Free |
| Key Vault | Standard | $0.6-0.8 |

**Note**: Actual costs depend on usage. See [Azure Pricing](https://azure.microsoft.com/en-us/pricing/) for details.

## Troubleshooting

### Azure Maps API errors
```bash
# Check Maps account status
az maps account show --name $MAPS_NAME --resource-group $RESOURCE_GROUP

# Regenerate keys if needed
az maps account keys renew --name $MAPS_NAME --resource-group $RESOURCE_GROUP --key primary
```

### OpenAI deployment issues
```bash
# Check deployments
az cognitiveservices account deployment list --name $OPENAI_NAME --resource-group $RESOURCE_GROUP

# Check account status
az cognitiveservices account show --name $OPENAI_NAME --resource-group $RESOURCE_GROUP
```

### Service Principal issues
```bash
# Check role assignments
az role assignment list --assignee $CLIENT_ID

# Grant additional roles if needed
az role assignment create --assignee $CLIENT_ID --role "Contributor" --scope "/subscriptions/{subscription-id}"
```

## Next Steps

1. Update `.env` with the credentials from steps 1-5
2. Test the application: `python src/main.py --mode query --query "What's the weather in Seattle?"`
3. Start the API server: `python src/api.py`
4. Access the Swagger UI: `http://localhost:8000/docs`
