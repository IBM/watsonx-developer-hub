#!/bin/bash
set -uo pipefail

# Deployment script for AutoAI orchestration resources.
# Run from the template root directory: ./deploy.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "Starting deployment of AutoAI orchestration resources..."
echo "========================================================="

# Check if .env file exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "❌ Error: .env file not found in $SCRIPT_DIR"
    echo "Copy template.env to .env and fill in the required values."
    exit 1
fi

# Step 1: Generate template files (toolkit.yaml, agent.yaml)
echo ""
echo "Step 1: Generating template files from AutoAI deployment..."
if python "$SCRIPT_DIR/scripts/generate_template.py"; then
    echo "✓ Template files generated successfully"
    echo "  - toolkit.yaml"
    echo "  - agent.yaml"
else
    echo "❌ Failed to generate template files"
    echo "Please ensure:"
    echo "  - Python dependencies from requirements-dev.txt are installed"
    echo "  - .env file contains valid credentials"
    echo "  - WATSONX_AUTOAI_DEPLOYMENT_ID is correct"
    exit 1
fi

# Step 2: Add connection
echo ""
echo "Step 2: Adding connection 'autoai-prediction-connection'..."
if orchestrate connections add -a autoai-prediction-connection 2>/dev/null; then
    echo "✓ Connection added successfully"
else
    echo "⚠ Failed to add connection (may already exist)"
fi

# Step 3: Load environment variables from .env file (secrets are not logged)
echo ""
echo "Step 3: Loading environment variables from .env file..."
set -a
# shellcheck disable=SC1091
source "$SCRIPT_DIR/.env"
set +a
if [ -n "${WATSONX_URL:-}" ] && [ -n "${WATSONX_API_KEY:-}" ] && [ -n "${WATSONX_SPACE_ID:-}" ] && [ -n "${WATSONX_AUTOAI_DEPLOYMENT_ID:-}" ]; then
    echo "✓ Environment variables loaded successfully"
else
    echo "❌ One or more required variables are missing from .env"
    exit 1
fi

# Step 4: Configure connections for both draft and live environments
echo ""
echo "Step 4: Configuring connections for draft and live environments..."

for env in draft live; do
    echo ""
    echo "  Configuring $env environment..."

    if orchestrate connections configure \
        -a autoai-prediction-connection \
        --env "$env" \
        --type team \
        --kind key_value 2>/dev/null; then
        echo "  ✓ Connection configured for $env environment"
    else
        echo "  ⚠ Failed to configure connection for $env environment"
        continue
    fi

    if orchestrate connections set-credentials \
        -a autoai-prediction-connection \
        --env "$env" \
        -e "WATSONX_URL=$WATSONX_URL" \
        -e "WATSONX_API_KEY=$WATSONX_API_KEY" \
        -e "WATSONX_SPACE_ID=$WATSONX_SPACE_ID" \
        -e "WATSONX_AUTOAI_DEPLOYMENT_ID=$WATSONX_AUTOAI_DEPLOYMENT_ID" 2>/dev/null; then
        echo "  ✓ Credentials set for $env environment"
    else
        echo "  ⚠ Failed to set credentials for $env environment"
    fi
done

# Step 5: Import toolkit
echo ""
echo "Step 5: Importing toolkit from toolkit.yaml..."
if [ ! -f "$SCRIPT_DIR/toolkit.yaml" ]; then
    echo "❌ Error: toolkit.yaml file not found"
    exit 1
fi

if orchestrate toolkits import -f "$SCRIPT_DIR/toolkit.yaml" -a autoai-prediction-connection 2>/dev/null; then
    echo "✓ Toolkit imported successfully"
else
    echo "⚠ Failed to import toolkit (may already exist or invalid configuration)"
fi

# Step 6: Import agent
echo ""
echo "Step 6: Importing agent from agent.yaml..."
if [ ! -f "$SCRIPT_DIR/agent.yaml" ]; then
    echo "❌ Error: agent.yaml file not found"
    exit 1
fi

if orchestrate agents import -f "$SCRIPT_DIR/agent.yaml" 2>/dev/null; then
    echo "✓ Agent imported successfully"
else
    echo "⚠ Failed to import agent (may already exist or invalid configuration)"
fi

# Step 7: Deploy agent
echo ""
echo "Step 7: Deploying agent 'autoai_prediction_agent'..."
if orchestrate agents deploy --name autoai_prediction_agent 2>/dev/null; then
    echo "✓ Agent deployed successfully"
else
    echo "⚠ Failed to deploy agent (may already be deployed or configuration error)"
fi

echo ""
echo "========================================================="
echo "Deployment process completed!"
echo ""
echo "To verify the deployment, you can run:"
echo "  orchestrate agents list"
echo "  orchestrate toolkits list"
echo "  orchestrate connections list"
