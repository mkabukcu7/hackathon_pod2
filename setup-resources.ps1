# Azure Resource Setup Script for hackathon_pod2 (PowerShell)
# This script creates all required Azure resources in one go

param(
    [string]$ResourceGroup = "hackathon-pod2-rg",
    [string]$Location = "eastus",
    [string]$Environment = "dev"
)

$ErrorActionPreference = "Stop"

# Configuration
$MAPS_NAME = "hackathon-maps-${Environment}"
$OPENAI_NAME = "hackathon-openai-${Environment}"
$KEYVAULT_NAME = "hackathon-kv-${Environment}-$(Get-Random -Minimum 1000 -Maximum 9999)"

# Functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check prerequisites
function Check-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    try {
        $version = az --version
    } catch {
        Write-Error-Custom "Azure CLI not found. Please install it: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    }
    
    try {
        $account = az account show --output json | ConvertFrom-Json
        $script:SUBSCRIPTION_ID = $account.id
        $script:TENANT_ID = $account.tenantId
        Write-Info "Using subscription: $SUBSCRIPTION_ID"
    } catch {
        Write-Error-Custom "Not logged in to Azure. Run: az login"
        exit 1
    }
}

# Create resource group
function New-ResourceGroup {
    Write-Info "Creating resource group: $ResourceGroup..."
    
    $exists = az group exists --name $ResourceGroup | ConvertFrom-Json
    
    if ($exists) {
        Write-Warn "Resource group already exists: $ResourceGroup"
    } else {
        az group create `
            --name $ResourceGroup `
            --location $Location
        Write-Info "Resource group created successfully"
    }
}

# Create Azure Maps
function New-AzureMaps {
    Write-Info "Creating Azure Maps: $MAPS_NAME..."
    
    try {
        az maps account show --name $MAPS_NAME --resource-group $ResourceGroup | Out-Null
        Write-Warn "Azure Maps already exists: $MAPS_NAME"
    } catch {
        az maps account create `
            --name $MAPS_NAME `
            --resource-group $ResourceGroup `
            --sku S0 `
            --kind Gen2
        Write-Info "Azure Maps created successfully"
    }
    
    $script:MAPS_KEY = az maps account keys list `
        --name $MAPS_NAME `
        --resource-group $ResourceGroup `
        --query "primaryKey" `
        --output tsv
    
    Write-Info "Azure Maps API Key: $($MAPS_KEY.Substring(0, 20))..."
}

# Create Azure OpenAI
function New-AzureOpenAI {
    Write-Info "Creating Azure OpenAI: $OPENAI_NAME..."
    
    try {
        az cognitiveservices account show --name $OPENAI_NAME --resource-group $ResourceGroup | Out-Null
        Write-Warn "Azure OpenAI already exists: $OPENAI_NAME"
    } catch {
        az cognitiveservices account create `
            --name $OPENAI_NAME `
            --resource-group $ResourceGroup `
            --kind OpenAI `
            --sku s0 `
            --location $Location `
            --yes
        Write-Info "Azure OpenAI created successfully"
    }
    
    $script:OPENAI_ENDPOINT = az cognitiveservices account show `
        --name $OPENAI_NAME `
        --resource-group $ResourceGroup `
        --query "properties.endpoint" `
        --output tsv
    
    $script:OPENAI_KEY = az cognitiveservices account keys list `
        --name $OPENAI_NAME `
        --resource-group $ResourceGroup `
        --query "key1" `
        --output tsv
    
    Write-Info "Azure OpenAI Endpoint: $OPENAI_ENDPOINT"
    Write-Info "Azure OpenAI API Key: $($OPENAI_KEY.Substring(0, 20))..."
}

# Deploy model
function Deploy-Model {
    param(
        [string]$Model,
        [string]$DeploymentName,
        [string]$Version
    )
    
    Write-Info "Deploying $Model as $DeploymentName..."
    
    try {
        az cognitiveservices account deployment show `
            --name $OPENAI_NAME `
            --resource-group $ResourceGroup `
            --deployment-name $DeploymentName | Out-Null
        Write-Warn "Deployment already exists: $DeploymentName"
    } catch {
        az cognitiveservices account deployment create `
            --name $OPENAI_NAME `
            --resource-group $ResourceGroup `
            --deployment-name $DeploymentName `
            --model-name $Model `
            --model-version $Version `
            --sku-capacity 1 `
            --sku-name "Standard"
        Write-Info "Model deployed successfully"
    }
    
    $script:OPENAI_DEPLOYMENT_NAME = $DeploymentName
}

# Create service principal
function New-ServicePrincipal {
    Write-Info "Creating service principal..."
    
    $spName = "hackathon-pod2-sp-${Environment}"
    
    $existing = az ad sp list --display-name $spName --query "[0].appId" -o tsv -e 2>$null
    
    if ($existing) {
        Write-Warn "Service principal already exists: $spName"
        $script:CLIENT_ID = $existing
        $script:CLIENT_SECRET = "(existing - retrieve from Key Vault or recreate)"
    } else {
        $spOutput = az ad sp create-for-rbac `
            --name $spName `
            --role "Reader" `
            --scopes "/subscriptions/$SUBSCRIPTION_ID" `
            --output json | ConvertFrom-Json
        
        $script:CLIENT_ID = $spOutput.appId
        $script:CLIENT_SECRET = $spOutput.password
        Write-Info "Service principal created successfully"
    }
    
    Write-Info "Service Principal Client ID: $CLIENT_ID"
    Write-Info "Service Principal Client Secret: $($CLIENT_SECRET.Substring(0, 20))..."
}

# Create Key Vault
function New-KeyVault {
    Write-Info "Creating Key Vault: $KEYVAULT_NAME..."
    
    try {
        az keyvault show --name $KEYVAULT_NAME --resource-group $ResourceGroup | Out-Null
        Write-Warn "Key Vault already exists: $KEYVAULT_NAME"
    } catch {
        az keyvault create `
            --name $KEYVAULT_NAME `
            --resource-group $ResourceGroup `
            --location $Location
        Write-Info "Key Vault created successfully"
    }
    
    # Store secrets
    Write-Info "Storing secrets in Key Vault..."
    
    az keyvault secret set `
        --vault-name $KEYVAULT_NAME `
        --name "AZURE-MAPS-API-KEY" `
        --value $MAPS_KEY | Out-Null
    
    az keyvault secret set `
        --vault-name $KEYVAULT_NAME `
        --name "AZURE-OPENAI-API-KEY" `
        --value $OPENAI_KEY | Out-Null
    
    az keyvault secret set `
        --vault-name $KEYVAULT_NAME `
        --name "AZURE-CLIENT-SECRET" `
        --value $CLIENT_SECRET | Out-Null
    
    Write-Info "Secrets stored in Key Vault"
}

# Generate .env file
function New-EnvFile {
    Write-Info "Generating .env file..."
    
    $envContent = @"
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY=$OPENAI_KEY
AZURE_OPENAI_DEPLOYMENT_NAME=$OPENAI_DEPLOYMENT_NAME
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Azure Resource Management
AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID
AZURE_TENANT_ID=$TENANT_ID
AZURE_CLIENT_ID=$CLIENT_ID
AZURE_CLIENT_SECRET=$CLIENT_SECRET

# Azure Maps Configuration (Weather and Environmental Data)
AZURE_MAPS_API_KEY=$MAPS_KEY

# Azure Key Vault (Optional)
AZURE_KEYVAULT_NAME=$KEYVAULT_NAME
AZURE_KEYVAULT_RESOURCE_GROUP=$ResourceGroup

# Application Settings
LOG_LEVEL=INFO
APP_PORT=8000
"@
    
    $envFile = ".env.generated"
    Set-Content -Path $envFile -Value $envContent
    
    Write-Info "Generated .env file: $envFile"
}

# Display summary
function Display-Summary {
    Write-Host ""
    Write-Host "======================================" -ForegroundColor Green
    Write-Host "Azure Resources Created Successfully!" -ForegroundColor Green
    Write-Host "======================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Resource Group: $ResourceGroup"
    Write-Host "Location: $Location"
    Write-Host ""
    Write-Host "Azure Maps:"
    Write-Host "  Name: $MAPS_NAME"
    Write-Host "  API Key: $($MAPS_KEY.Substring(0, 20))..."
    Write-Host ""
    Write-Host "Azure OpenAI:"
    Write-Host "  Name: $OPENAI_NAME"
    Write-Host "  Endpoint: $OPENAI_ENDPOINT"
    Write-Host "  Deployment: $OPENAI_DEPLOYMENT_NAME"
    Write-Host "  API Key: $($OPENAI_KEY.Substring(0, 20))..."
    Write-Host ""
    Write-Host "Service Principal:"
    Write-Host "  Client ID: $CLIENT_ID"
    Write-Host "  Tenant ID: $TENANT_ID"
    Write-Host ""
    Write-Host "Key Vault:"
    Write-Host "  Name: $KEYVAULT_NAME"
    Write-Host ""
    Write-Host "Generated .env file: .env.generated" -ForegroundColor Yellow
    Write-Host "Review and merge with your .env file" -ForegroundColor Yellow
    Write-Host ""
}

# Main execution
Write-Host "Azure Resource Setup for hackathon_pod2" -ForegroundColor Green
Write-Host ""

Check-Prerequisites
New-ResourceGroup
New-AzureMaps
New-AzureOpenAI
Deploy-Model -Model "gpt-35-turbo" -DeploymentName "gpt-35-turbo" -Version "0613"
New-ServicePrincipal
New-KeyVault
New-EnvFile
Display-Summary
