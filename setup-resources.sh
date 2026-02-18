#!/bin/bash

# Azure Resource Setup Script for hackathon_pod2
# This script creates all required Azure resources in one go

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-hackathon-pod2-rg}"
LOCATION="${LOCATION:-eastus}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
MAPS_NAME="hackathon-maps-${ENVIRONMENT}"
OPENAI_NAME="hackathon-openai-${ENVIRONMENT}"
KEYVAULT_NAME="hackathon-kv-${ENVIRONMENT}-$(date +%s | tail -c 5)"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI not found. Please install it: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
    
    if ! az account show &> /dev/null; then
        log_error "Not logged in to Azure. Run: az login"
        exit 1
    fi
    
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    TENANT_ID=$(az account show --query tenantId -o tsv)
    log_info "Using subscription: $SUBSCRIPTION_ID"
}

# Create resource group
create_resource_group() {
    log_info "Creating resource group: $RESOURCE_GROUP..."
    
    if az group exists --name "$RESOURCE_GROUP" | grep -q true; then
        log_warn "Resource group already exists: $RESOURCE_GROUP"
    else
        az group create \
            --name "$RESOURCE_GROUP" \
            --location "$LOCATION"
        log_info "Resource group created successfully"
    fi
}

# Create Azure Maps
create_maps() {
    log_info "Creating Azure Maps: $MAPS_NAME..."
    
    if az maps account show --name "$MAPS_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
        log_warn "Azure Maps already exists: $MAPS_NAME"
    else
        az maps account create \
            --name "$MAPS_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --sku S0 \
            --kind Gen2
        log_info "Azure Maps created successfully"
    fi
    
    MAPS_KEY=$(az maps account keys list \
        --name "$MAPS_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "primaryKey" \
        --output tsv)
    
    log_info "Azure Maps API Key: $MAPS_KEY"
}

# Create Azure OpenAI
create_openai() {
    log_info "Creating Azure OpenAI: $OPENAI_NAME..."
    
    if az cognitiveservices account show --name "$OPENAI_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
        log_warn "Azure OpenAI already exists: $OPENAI_NAME"
    else
        az cognitiveservices account create \
            --name "$OPENAI_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --kind OpenAI \
            --sku s0 \
            --location "$LOCATION" \
            --yes
        log_info "Azure OpenAI created successfully"
    fi
    
    OPENAI_ENDPOINT=$(az cognitiveservices account show \
        --name "$OPENAI_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.endpoint" \
        --output tsv)
    
    OPENAI_KEY=$(az cognitiveservices account keys list \
        --name "$OPENAI_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "key1" \
        --output tsv)
    
    log_info "Azure OpenAI Endpoint: $OPENAI_ENDPOINT"
    log_info "Azure OpenAI API Key: $OPENAI_KEY"
}

# Deploy model
deploy_model() {
    local model=$1
    local deployment=$2
    local version=$3
    
    log_info "Deploying $model as $deployment..."
    
    if az cognitiveservices account deployment show \
        --name "$OPENAI_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --deployment-name "$deployment" &>/dev/null; then
        log_warn "Deployment already exists: $deployment"
    else
        az cognitiveservices account deployment create \
            --name "$OPENAI_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --deployment-name "$deployment" \
            --model-name "$model" \
            --model-version "$version" \
            --sku-capacity 1 \
            --sku-name "Standard"
        log_info "Model deployed successfully"
    fi
    
    OPENAI_DEPLOYMENT_NAME=$deployment
}

# Create service principal
create_service_principal() {
    log_info "Creating service principal..."
    
    SP_NAME="hackathon-pod2-sp-${ENVIRONMENT}"
    
    if az ad sp list --display-name "$SP_NAME" --query "[0].id" -o tsv | grep -q .; then
        log_warn "Service principal already exists: $SP_NAME"
        CLIENT_ID=$(az ad sp list --display-name "$SP_NAME" --query "[0].appId" -o tsv)
        CLIENT_SECRET="(existing - retrieve from Key Vault or recreate with new password)"
    else
        SP_OUTPUT=$(az ad sp create-for-rbac \
            --name "$SP_NAME" \
            --role "Reader" \
            --scopes "/subscriptions/$SUBSCRIPTION_ID" \
            --output json)
        
        CLIENT_ID=$(echo "$SP_OUTPUT" | jq -r '.appId')
        CLIENT_SECRET=$(echo "$SP_OUTPUT" | jq -r '.password')
        log_info "Service principal created successfully"
    fi
    
    log_info "Service Principal Client ID: $CLIENT_ID"
    log_info "Service Principal Client Secret: $CLIENT_SECRET"
}

# Create Key Vault
create_keyvault() {
    log_info "Creating Key Vault: $KEYVAULT_NAME..."
    
    if az keyvault show --name "$KEYVAULT_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
        log_warn "Key Vault already exists: $KEYVAULT_NAME"
    else
        az keyvault create \
            --name "$KEYVAULT_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --location "$LOCATION"
        log_info "Key Vault created successfully"
    fi
    
    # Store secrets
    log_info "Storing secrets in Key Vault..."
    
    az keyvault secret set \
        --vault-name "$KEYVAULT_NAME" \
        --name "AZURE-MAPS-API-KEY" \
        --value "$MAPS_KEY" &>/dev/null
    
    az keyvault secret set \
        --vault-name "$KEYVAULT_NAME" \
        --name "AZURE-OPENAI-API-KEY" \
        --value "$OPENAI_KEY" &>/dev/null
    
    az keyvault secret set \
        --vault-name "$KEYVAULT_NAME" \
        --name "AZURE-CLIENT-SECRET" \
        --value "$CLIENT_SECRET" &>/dev/null
    
    log_info "Secrets stored in Key Vault"
}

# Generate .env file
generate_env() {
    log_info "Generating .env file..."
    
    ENV_FILE=".env.generated"
    
    cat > "$ENV_FILE" << EOF
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
AZURE_KEYVAULT_RESOURCE_GROUP=$RESOURCE_GROUP

# Application Settings
LOG_LEVEL=INFO
APP_PORT=8000
EOF
    
    log_info "Generated .env file: $ENV_FILE"
    log_warn "IMPORTANT: Review and merge with your existing .env file, or rename to .env"
}

# Display summary
display_summary() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Azure Resources Created Successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Location: $LOCATION"
    echo ""
    echo "Azure Maps:"
    echo "  Name: $MAPS_NAME"
    echo "  API Key: ${MAPS_KEY:0:20}..."
    echo ""
    echo "Azure OpenAI:"
    echo "  Name: $OPENAI_NAME"
    echo "  Endpoint: $OPENAI_ENDPOINT"
    echo "  Deployment: $OPENAI_DEPLOYMENT_NAME"
    echo "  API Key: ${OPENAI_KEY:0:20}..."
    echo ""
    echo "Service Principal:"
    echo "  Client ID: $CLIENT_ID"
    echo "  Tenant ID: $TENANT_ID"
    echo ""
    echo "Key Vault:"
    echo "  Name: $KEYVAULT_NAME"
    echo ""
    echo -e "${YELLOW}Generated .env file: .env.generated${NC}"
    echo -e "${YELLOW}Review and merge with your .env file${NC}"
    echo ""
}

# Main execution
main() {
    echo -e "${GREEN}Azure Resource Setup for hackathon_pod2${NC}"
    echo ""
    
    check_prerequisites
    create_resource_group
    create_maps
    create_openai
    deploy_model "gpt-35-turbo" "gpt-35-turbo" "0613"
    create_service_principal
    create_keyvault
    generate_env
    display_summary
}

# Run main
main "$@"
