#!/bin/bash
set -uo pipefail

# Cleanup script for AutoAI orchestration resources.
# Run from the template root directory: ./scripts/cleanup.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Starting cleanup of AutoAI orchestration resources..."
echo "=================================================="

echo ""
echo "Step 1: Undeploying agent 'autoai_prediction_agent'..."
if orchestrate agents undeploy --name autoai_prediction_agent 2>/dev/null; then
    echo "✓ Agent undeployed successfully"
else
    echo "⚠ Failed to undeploy agent (may not exist or already undeployed)"
fi

echo ""
echo "Step 2: Removing agent 'autoai_prediction_agent'..."
if orchestrate agents remove --name autoai_prediction_agent --kind native 2>/dev/null; then
    echo "✓ Agent removed successfully"
else
    echo "⚠ Failed to remove agent (may not exist)"
fi

echo ""
echo "Step 3: Removing toolkit 'autoai-generic-toolkit'..."
if orchestrate toolkits remove --name autoai-generic-toolkit 2>/dev/null; then
    echo "✓ Toolkit removed successfully"
else
    echo "⚠ Failed to remove toolkit (may not exist)"
fi

echo ""
echo "Step 4: Removing connection 'autoai-prediction-connection'..."
if orchestrate connections remove --app-id autoai-prediction-connection 2>/dev/null; then
    echo "✓ Connection removed successfully"
else
    echo "⚠ Failed to remove connection (may not exist)"
fi

echo ""
echo "Step 5: Removing locally generated artifacts..."
rm -f "$ROOT_DIR/toolkit.yaml" "$ROOT_DIR/agent.yaml"
echo "✓ Removed toolkit.yaml, agent.yaml (if present)"

echo ""
echo "=================================================="
echo "Cleanup process completed!"
echo "Note: Warnings indicate resources that were already removed or never existed."
