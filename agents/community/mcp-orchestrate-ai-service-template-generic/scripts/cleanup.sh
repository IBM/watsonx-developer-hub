#!/bin/bash

# Cleanup script for AI Service orchestration resources
# This script removes all created items with individual error handling
# Each deletion is wrapped in a try-catch equivalent to handle non-existent resources

echo "Starting cleanup of AI Service orchestration resources..."
echo "========================================================="

# Step 1: Undeploy the agent
echo ""
echo "Step 1: Undeploying agent 'ai_services_agent_v3'..."
if orchestrate agents undeploy --name ai_services_agent_v3 2>/dev/null; then
    echo "✓ Agent undeployed successfully"
else
    echo "⚠ Failed to undeploy agent (may not exist or already undeployed)"
fi

# Step 2: Remove the agent
echo ""
echo "Step 2: Removing agent 'ai_services_agent_v3'..."
if orchestrate agents remove --name ai_services_agent_v3 --kind native 2>/dev/null; then
    echo "✓ Agent removed successfully"
else
    echo "⚠ Failed to remove agent (may not exist)"
fi

# Step 3: Remove the toolkit
echo ""
echo "Step 3: Removing toolkit 'ai-services-toolkit-v3'..."
if orchestrate toolkits remove --name ai-services-toolkit-v3 2>/dev/null; then
    echo "✓ Toolkit removed successfully"
else
    echo "⚠ Failed to remove toolkit (may not exist)"
fi

# Step 4: Remove the connection
echo ""
echo "Step 4: Removing connection 'ai-service-connection'..."
if orchestrate connections remove --app-id ai-service-connection 2>/dev/null; then
    echo "✓ Connection removed successfully"
else
    echo "⚠ Failed to remove connection (may not exist)"
fi

echo ""
echo "=================================================="
echo "Cleanup process completed!"
echo "Note: Warnings indicate resources that were already removed or never existed."
