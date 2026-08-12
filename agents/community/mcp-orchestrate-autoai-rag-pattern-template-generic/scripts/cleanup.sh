#!/bin/bash

# Cleanup script for AutoAI RAG Pattern orchestration resources
# This script removes all created items with individual error handling
# Each deletion is wrapped in a try-catch equivalent to handle non-existent resources

echo "Starting cleanup of AutoAI RAG Pattern orchestration resources..."
echo "=================================================="

# Step 1: Undeploy the agent
echo ""
echo "Step 1: Undeploying agent 'autoai_rag_pattern_agent_v3'..."
if orchestrate agents undeploy --name autoai_rag_pattern_agent_v3 2>/dev/null; then
    echo "✓ Agent undeployed successfully"
else
    echo "⚠ Failed to undeploy agent (may not exist or already undeployed)"
fi

# Step 2: Remove the agent
echo ""
echo "Step 2: Removing agent 'autoai_rag_pattern_agent_v3'..."
if orchestrate agents remove --name autoai_rag_pattern_agent_v3 --kind native 2>/dev/null; then
    echo "✓ Agent removed successfully"
else
    echo "⚠ Failed to remove agent (may not exist)"
fi

# Step 3: Remove the toolkit
echo ""
echo "Step 3: Removing toolkit 'autoai-rag-pattern-toolkit-v3'..."
if orchestrate toolkits remove --name autoai-rag-pattern-toolkit-v3 2>/dev/null; then
    echo "✓ Toolkit removed successfully"
else
    echo "⚠ Failed to remove toolkit (may not exist)"
fi

# Step 4: Remove the connection
echo ""
echo "Step 4: Removing connection 'autoai-rag-pattern-connection'..."
if orchestrate connections remove --app-id autoai-rag-pattern-connection 2>/dev/null; then
    echo "✓ Connection removed successfully"
else
    echo "⚠ Failed to remove connection (may not exist)"
fi

echo ""
echo "=================================================="
echo "Cleanup process completed!"
echo "Note: Warnings indicate resources that were already removed or never existed."
