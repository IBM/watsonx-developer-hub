#!/bin/bash
set -uo pipefail

# Cleanup script for AutoAI orchestration resources.
# Run from the template root directory: ./scripts/cleanup.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Starting cleanup of AutoAI orchestration resources..."
echo "=================================================="

# ── Pre-flight checks ────────────────────────────────────────────────────────

if ! command -v orchestrate &> /dev/null; then
    echo "❌ Error: 'orchestrate' CLI not found in PATH"
    echo "   Install it with: pip install ibm-watsonx-orchestrate"
    exit 1
fi

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

# Tracks whether any step produced a real (non-"not found") error.
ERRORS=0

# Helper: checks output text for any "resource does not exist" signal.
# The CLI sometimes exits 0 with a [WARNING] instead of a non-zero exit code.
_is_not_found() {
    echo "$1" | grep -qi "not found\|does not exist\|not deployed\|no .* found\|failed to get"
}

# ── Step 1: Undeploy agent ───────────────────────────────────────────────────
echo ""
echo "Step 1: Undeploying agent 'autoai_prediction_agent'..."
undep_output=$(orchestrate agents undeploy --name autoai_prediction_agent 2>&1)
undep_exit=$?
if _is_not_found "$undep_output"; then
    echo "  ℹ️  Agent not deployed — skipping"
elif [ $undep_exit -eq 0 ]; then
    echo "✓ Agent undeployed successfully"
else
    echo "⚠ Failed to undeploy agent (continuing):"
    echo "  $undep_output"
    ERRORS=$((ERRORS + 1))
fi

# ── Step 2: Remove agent ─────────────────────────────────────────────────────
echo ""
echo "Step 2: Removing agent 'autoai_prediction_agent'..."
rem_ag_output=$(orchestrate agents remove --name autoai_prediction_agent --kind native 2>&1)
rem_ag_exit=$?
if _is_not_found "$rem_ag_output"; then
    echo "  ℹ️  Agent not found — skipping"
elif [ $rem_ag_exit -eq 0 ]; then
    echo "✓ Agent removed successfully"
else
    echo "⚠ Failed to remove agent (continuing):"
    echo "  $rem_ag_output"
    ERRORS=$((ERRORS + 1))
fi

# ── Step 3: Remove toolkit ───────────────────────────────────────────────────
echo ""
echo "Step 3: Removing toolkit 'autoai-generic-toolkit'..."
rem_tk_output=$(orchestrate toolkits remove --name autoai-generic-toolkit 2>&1)
rem_tk_exit=$?
if _is_not_found "$rem_tk_output"; then
    echo "  ℹ️  Toolkit not found — skipping"
elif [ $rem_tk_exit -eq 0 ]; then
    echo "✓ Toolkit removed successfully"
else
    echo "⚠ Failed to remove toolkit (continuing):"
    echo "  $rem_tk_output"
    ERRORS=$((ERRORS + 1))
fi

# ── Step 4: Remove connection ────────────────────────────────────────────────
echo ""
echo "Step 4: Removing connection 'autoai-prediction-connection'..."
rem_con_output=$(orchestrate connections remove --app-id autoai-prediction-connection 2>&1)
rem_con_exit=$?
if _is_not_found "$rem_con_output"; then
    echo "  ℹ️  Connection not found — skipping"
elif [ $rem_con_exit -eq 0 ]; then
    echo "✓ Connection removed successfully"
else
    echo "⚠ Failed to remove connection (continuing):"
    echo "  $rem_con_output"
    ERRORS=$((ERRORS + 1))
fi

# ── Step 5: Remove locally generated artifacts ───────────────────────────────
echo ""
echo "Step 5: Removing locally generated artifacts..."
removed=()
for artifact in "$ROOT_DIR/toolkit.yaml" "$ROOT_DIR/agent.yaml"; do
    if [ -f "$artifact" ]; then
        rm -f "$artifact"
        removed+=("$(basename "$artifact")")
    fi
done
if [ ${#removed[@]} -gt 0 ]; then
    echo "✓ Removed: ${removed[*]}"
else
    echo "  ℹ️  No generated artifacts found — skipping"
fi

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "=================================================="
if [ $ERRORS -eq 0 ]; then
    echo "✓ Cleanup complete!"
else
    echo "⚠ Cleanup complete with $ERRORS warning(s) — see output above."
fi
