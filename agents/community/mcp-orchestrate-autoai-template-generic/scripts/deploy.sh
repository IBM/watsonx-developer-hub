#!/bin/bash
set -uo pipefail

# Deployment script for AutoAI orchestration resources.
# Run from the template root directory: ./scripts/deploy.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR" || exit 1

echo "Starting deployment of AutoAI orchestration resources..."
echo "========================================================="

# ── Pre-flight checks ────────────────────────────────────────────────────────

# Check if .env file exists
if [ ! -f "$ROOT_DIR/.env" ]; then
    echo "❌ Error: .env file not found in $ROOT_DIR"
    echo "   Copy template.env to .env and fill in the required values."
    exit 1
fi

# Check that the orchestrate CLI is available
if ! command -v orchestrate &> /dev/null; then
    echo "❌ Error: 'orchestrate' CLI not found in PATH"
    echo "   Install it with: pip install ibm-watsonx-orchestrate"
    exit 1
fi

# Check that the active Orchestrate session token is valid.
# 'orchestrate env list' is a lightweight read-only call that requires auth.
echo ""
echo "Pre-flight: Checking Orchestrate authentication..."
if ! orchestrate env list &> /dev/null; then
    echo "❌ Error: Orchestrate session token is missing or expired."
    echo ""
    echo "   Run the following command, then re-run this script:"
    echo "     orchestrate env activate <your-env-name>"
    echo ""
    echo "   To list available environments:"
    echo "     orchestrate env list --all"
    exit 1
fi
echo "✓ Orchestrate authentication OK"

# ── Step 1: Generate template files ──────────────────────────────────────────
echo ""
echo "Step 1: Generating template files from AutoAI deployment..."
if python "$SCRIPT_DIR/generate_template.py"; then
    echo "✓ Template files generated successfully"
    echo "  - toolkit.yaml"
    echo "  - agent.yaml"
else
    echo "❌ Failed to generate template files"
    echo "   Please ensure:"
    echo "   - Python dependencies from requirements-dev.txt are installed"
    echo "   - .env file contains valid watsonx.ai credentials"
    echo "   - WATSONX_AUTOAI_DEPLOYMENT_ID is correct"
    exit 1
fi

# ── Step 2: Load .env into the shell (for set-credentials) ───────────────────
echo ""
echo "Step 2: Loading environment variables from .env..."
set -a
# shellcheck disable=SC1091
source "$ROOT_DIR/.env"
set +a
if [ -n "${WATSONX_URL:-}" ] && [ -n "${WATSONX_API_KEY:-}" ] \
   && [ -n "${WATSONX_SPACE_ID:-}" ] && [ -n "${WATSONX_AUTOAI_DEPLOYMENT_ID:-}" ]; then
    echo "✓ Environment variables loaded"
else
    echo "❌ One or more required variables are missing from .env:"
    echo "   WATSONX_URL, WATSONX_API_KEY, WATSONX_SPACE_ID, WATSONX_AUTOAI_DEPLOYMENT_ID"
    exit 1
fi

# ── Step 3: Add connection ────────────────────────────────────────────────────
echo ""
echo "Step 3: Adding connection 'autoai-prediction-connection'..."
add_output=$(orchestrate connections add -a autoai-prediction-connection 2>&1)
add_exit=$?
if [ $add_exit -eq 0 ]; then
    echo "✓ Connection added successfully"
elif echo "$add_output" | grep -qi "already exist\|already been\|already registered"; then
    echo "  (connection already exists — skipping)"
else
    echo "❌ Failed to add connection:"
    echo "$add_output"
    exit 1
fi

# ── Step 4: Configure connection for draft and live environments ──────────────
echo ""
echo "Step 4: Configuring connection credentials for draft and live environments..."
for env in draft live; do
    echo ""
    echo "  [$env] Configuring..."

    cfg_output=$(orchestrate connections configure \
        -a autoai-prediction-connection \
        --env "$env" \
        --type team \
        --kind key_value 2>&1)
    cfg_exit=$?
    if [ $cfg_exit -ne 0 ] && ! echo "$cfg_output" | grep -qi "already exist\|already been\|already registered"; then
        echo "  ❌ Failed to configure connection for $env:"
        echo "$cfg_output"
        exit 1
    fi
    echo "  ✓ Connection configured for $env"

    cred_output=$(orchestrate connections set-credentials \
        -a autoai-prediction-connection \
        --env "$env" \
        -e "WATSONX_URL=$WATSONX_URL" \
        -e "WATSONX_API_KEY=$WATSONX_API_KEY" \
        -e "WATSONX_SPACE_ID=$WATSONX_SPACE_ID" \
        -e "WATSONX_AUTOAI_DEPLOYMENT_ID=$WATSONX_AUTOAI_DEPLOYMENT_ID" 2>&1)
    cred_exit=$?
    if [ $cred_exit -ne 0 ]; then
        echo "  ❌ Failed to set credentials for $env:"
        echo "$cred_output"
        exit 1
    fi
    echo "  ✓ Credentials set for $env"
done

# ── Step 5: Import toolkit ────────────────────────────────────────────────────
echo ""
echo "Step 5: Importing toolkit from toolkit.yaml..."
if [ ! -f "$ROOT_DIR/toolkit.yaml" ]; then
    echo "❌ Error: toolkit.yaml not found (generation in Step 1 may have failed)"
    exit 1
fi

tk_output=$(orchestrate toolkits import -f "$ROOT_DIR/toolkit.yaml" -a autoai-prediction-connection 2>&1)
tk_exit=$?
if [ $tk_exit -eq 0 ]; then
    echo "✓ Toolkit imported successfully"
elif echo "$tk_output" | grep -qi "already exist\|already been\|already registered"; then
    echo "  (toolkit already exists — skipping)"
else
    echo "❌ Failed to import toolkit:"
    echo "$tk_output"
    exit 1
fi

# ── Step 6: Import agent ──────────────────────────────────────────────────────
echo ""
echo "Step 6: Importing agent from agent.yaml..."
if [ ! -f "$ROOT_DIR/agent.yaml" ]; then
    echo "❌ Error: agent.yaml not found (generation in Step 1 may have failed)"
    exit 1
fi

ag_output=$(orchestrate agents import -f "$ROOT_DIR/agent.yaml" 2>&1)
ag_exit=$?
if [ $ag_exit -eq 0 ]; then
    echo "✓ Agent imported successfully"
elif echo "$ag_output" | grep -qi "already exist\|already been\|already registered"; then
    echo "  (agent already exists — skipping)"
else
    echo "❌ Failed to import agent:"
    echo "$ag_output"
    exit 1
fi

# ── Step 7: Deploy agent ──────────────────────────────────────────────────────
echo ""
echo "Step 7: Deploying agent 'autoai_prediction_agent'..."
dep_output=$(orchestrate agents deploy --name autoai_prediction_agent 2>&1)
dep_exit=$?
if [ $dep_exit -eq 0 ]; then
    echo "✓ Agent deployed successfully"
elif echo "$dep_output" | grep -qi "already deployed\|already exist\|already been\|already registered"; then
    echo "  (agent already deployed — skipping)"
else
    echo "❌ Failed to deploy agent:"
    echo "$dep_output"
    exit 1
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "========================================================="
echo "✓ Deployment complete!"
echo ""
echo "To verify:"
echo "  orchestrate agents list"
echo "  orchestrate toolkits list"
echo "  orchestrate connections list"
