#!/bin/bash

# Deployment script for AI Service orchestration resources
# This script creates and configures all required resources with individual error handling
# Each step is wrapped in a try-catch equivalent to handle errors gracefully

echo "Starting deployment of AI Service orchestration resources..."
echo "===================================================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found in current directory"
    echo "Please create a .env file with required environment variables"
    exit 1
fi

# Step 1: Generate template files (toolkit.yaml, agent.yaml, generated_config.py)
echo ""
echo "Step 1: Generating template files from AI Service deployment..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if python "$SCRIPT_DIR/generate_template.py" 2>/dev/null; then
    echo "✓ Template files generated successfully"
    echo "  - toolkit.yaml"
    echo "  - agent.yaml"
    echo "  - mcp_server/generated_config.py"
else
    echo "❌ Failed to generate template files"
    echo "Please ensure:"
    echo "  - Python dependencies are installed (ibm-watsonx-ai, python-dotenv, pyyaml)"
    echo "  - .env file contains valid credentials"
    echo "  - WATSONX_AI_SERVICE_DEPLOYMENT_ID is correct"
    exit 1
fi

# Step 2: Add connection
echo ""
echo "Step 2: Adding connection 'ai-service-connection'..."
if orchestrate connections add -a ai-service-connection 2>/dev/null; then
    echo "✓ Connection added successfully"
else
    echo "⚠ Failed to add connection (may already exist)"
fi

# Step 3: Export environment variables from .env file
echo ""
echo "Step 3: Loading environment variables from .env file..."
if export $(grep -v '^#' .env | xargs) 2>/dev/null; then
    echo "✓ Environment variables loaded successfully"
    echo "  - WATSONX_URL: ${WATSONX_URL:0:30}..."
    echo "  - WATSONX_API_KEY: ${WATSONX_API_KEY:0:10}..."
    echo "  - WATSONX_SPACE_ID: $WATSONX_SPACE_ID"
    echo "  - WATSONX_AI_SERVICE_DEPLOYMENT_ID: $WATSONX_AI_SERVICE_DEPLOYMENT_ID"
else
    echo "❌ Failed to load environment variables from .env file"
    exit 1
fi

# Step 4: Configure connections for both draft and live environments
echo ""
echo "Step 4: Configuring connections for draft and live environments..."

for env in draft live; do
    echo ""
    echo "  Configuring $env environment..."
    
    # Configure connection
    if orchestrate connections configure \
        -a ai-service-connection \
        --env $env \
        --type team \
        --kind key_value 2>/dev/null; then
        echo "  ✓ Connection configured for $env environment"
    else
        echo "  ⚠ Failed to configure connection for $env environment"
        continue
    fi
    
    # Set credentials
    if orchestrate connections set-credentials \
        -a ai-service-connection \
        --env $env \
        -e "WATSONX_URL=$WATSONX_URL" \
        -e "WATSONX_API_KEY=$WATSONX_API_KEY" \
        -e "WATSONX_SPACE_ID=$WATSONX_SPACE_ID" \
        -e "WATSONX_AI_SERVICE_DEPLOYMENT_ID=$WATSONX_AI_SERVICE_DEPLOYMENT_ID" 2>/dev/null; then
        echo "  ✓ Credentials set for $env environment"
    else
        echo "  ⚠ Failed to set credentials for $env environment"
    fi
done

# Step 5: Import toolkit
echo ""
echo "Step 5: Importing toolkit from toolkit.yaml..."
if [ ! -f toolkit.yaml ]; then
    echo "❌ Error: toolkit.yaml file not found in current directory"
    exit 1
fi

if orchestrate toolkits import -f toolkit.yaml -a ai-service-connection 2>/dev/null; then
    echo "✓ Toolkit imported successfully"
else
    echo "⚠ Failed to import toolkit (may already exist or invalid configuration)"
fi

# Step 6: Import agent
echo ""
echo "Step 6: Importing agent from agent.yaml..."
if [ ! -f agent.yaml ]; then
    echo "❌ Error: agent.yaml file not found in current directory"
    exit 1
fi

if orchestrate agents import -f agent.yaml 2>/dev/null; then
    echo "✓ Agent imported successfully"
else
    echo "⚠ Failed to import agent (may already exist or invalid configuration)"
fi

# Step 7: Deploy agent
echo ""
echo "Step 7: Deploying agent 'ai_services_agent_v1'..."
if orchestrate agents deploy --name ai_services_agent_v1 2>/dev/null; then
    echo "✓ Agent deployed successfully"
else
    echo "⚠ Failed to deploy agent (may already be deployed or configuration error)"
fi

echo ""
echo "========================================================="
echo "Deployment process completed!"
echo "Note: Warnings indicate resources that already exist or configuration issues."
echo ""
echo "To verify the deployment, you can run:"
echo "  orchestrate agents list"
echo "  orchestrate toolkits list"
echo "  orchestrate connections list"
