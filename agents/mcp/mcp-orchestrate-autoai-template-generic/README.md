# Build a Conversational Agent with any watsonx.ai Model and IBM watsonx Orchestrate

**IBM watsonx · Complete Template & Tutorial**

A comprehensive guide to deploying any watsonx.ai model (classification, regression, custom) as an intelligent conversational agent using the **mcp-orchestrate-autoai-template-generic** template. This template and tutorial cover setup, deployment, troubleshooting, and advanced patterns.

**Template:** mcp-orchestrate-autoai-template-generic  
**Tags:** MCP Server | Any Deployed Model | Production-ready

---

## Table of Contents

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Step-by-Step Tutorial](#step-by-step-tutorial)
  - [Step 1: Prepare Your Model](#step-1--prepare-your-model-in-watsonxai)
  - [Step 2: Download & Setup Template](#step-2--download-the-template)
  - [Step 3: Configure Environment](#step-3--configure-the-environment)
  - [Step 4: Generate Configs](#step-4--generate-configs-from-your-deployment)
  - [Step 5: Set Up Orchestrate CLI](#step-5--set-up-the-watsonx-orchestrate-cli)
  - [Step 6: Deploy Agent](#step-6--deploy-the-agent)
  - [Step 7: Chat with Agent](#step-7--chat-with-your-agent)
- [MCP Server Explanation](#understanding-the-mcp-server-setup)
- [Updating Models](#updating-or-switching-models)
- [Local Testing](#running-the-mcp-server-locally)
- [Quick Reference](#quick-reference--full-command-sequence)
- [Known Limitations](#known-limitations)

---

## Introduction

This template demonstrates how to build a generic IBM watsonx Orchestrate agent that exposes predictions from **any** deployed model in watsonx.ai as an MCP tool. Works with AutoAI experiments, scikit-learn models, XGBoost, custom Python models, and more.

The MCP server fetches the model's input schema and target column **dynamically from the watsonx API at startup** - no hand-written config files are needed. `toolkit.yaml` and `agent.yaml` are build-time artifacts generated locally by `scripts/generate_template.py` based on the actual deployment.

**Key benefits:**

- Works with **any** watsonx.ai deployed model: Classification, regression, custom outputs
- Zero hand-coded configuration required
- Dynamic schema fetching at runtime
- Production-ready, fully generic template
- One-command deployment pipeline

---

## Prerequisites

| Requirement                          | Notes                                                                                                      |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| **Python 3.10+**                     | Required for both the generator and the MCP server runtime.                                                |
| **IBM watsonx.ai access**            | Active IBM Cloud account with watsonx.ai service provisioned.                                              |
| **A deployed model**                 | Any model trained and deployed to a watsonx.ai online endpoint (classification, regression, custom, etc.). |
| **Deployment ID**                    | The `deployment_id` of your deployed model (visible in the watsonx.ai UI).                                 |
| **Space ID**                         | The `space_id` of the deployment space in watsonx.ai.                                                      |
| **watsonx.ai API Key**               | An IBM Cloud IAM API key with access to your watsonx.ai instance.                                          |
| **IBM watsonx Orchestrate instance** | An active Orchestrate instance with a known URL and API key.                                               |

---

## Architecture Overview

### Directory Structure

```
mcp-orchestrate-autoai-template-generic/
 ┣ LICENSE
 ┣ README.md
 ┣ template.env              ← copy to .env, fill credentials
 ┣ .gitignore
 ┣ requirements-dev.txt      ← local deps (generator + orchestrate CLI)
 ┣ scripts/
 ┃  ┣ generate_template.py   ← queries watsonx.ai, writes YAMLs
 ┃  ┣ deploy.sh              ← one-shot: generate + import + deploy
 ┃  ┗ cleanup.sh             ← removes all Orchestrate resources
 ┣ mcp_server/
 ┃  ┣ server.py              ← FastMCP server, exposes the tool
 ┃  ┣ utils.py               ← schema fetching, scoring, validation
 ┃  ┗ requirements.txt       ← runtime deps (packaged into Orchestrate)
 ┣ toolkit.yaml              ← GENERATED at deploy time
 ┗ agent.yaml                ← GENERATED at deploy time
```

### Key Components

- **`template.env`**: Template with placeholders for required environment variables.
- **`requirements-dev.txt`**: Local dependencies for the generator script and Orchestrate CLI.
- **`scripts/generate_template.py`**: Queries watsonx.ai, writes `toolkit.yaml` and `agent.yaml`.
- **`scripts/deploy.sh`**: One-command deployment (generates + imports + deploys).
- **`scripts/cleanup.sh`**: Removes all Orchestrate resources and local artifacts.
- **`mcp_server/server.py`**: MCP server that exposes the `get_prediction` tool.
- **`mcp_server/utils.py`**: Dynamic schema fetching, scoring helpers, validation.
- **`mcp_server/requirements.txt`**: Runtime dependencies (packaged into Orchestrate).

---

## Step-by-Step Tutorial

### Step 1 - Prepare Your Model in watsonx.ai

#### Option A: Use an Existing Deployment

If you already have a model deployed in watsonx.ai, you just need the **Deployment ID** from your deployment's details page. Skip to Step 2.

#### Option B: Train and Deploy a New Model

The template works with any model type: AutoAI experiments, custom Python models, scikit-learn, XGBoost, or any WML asset.

**Example scenario used in this tutorial:** Customer risk scoring model predicting churn risk (0–1) based on tenure, account balance, and support ticket count.

**How to train and deploy:**

1. **Use IBM's AutoAI samples** (easiest):
   - Visit [watsonx-ai-samples repository](https://github.com/IBM/watsonx-ai-samples/tree/master/cloud/notebooks/python_sdk/experiments/autoai)
   - Run any notebook in a watsonx.ai notebook session
   - The notebook will train and deploy a model automatically

2. **Use the watsonx.ai UI**:
   - Open [watsonx.ai](https://dataplatform.cloud.ibm.com/wx/home?context=wx)
   - Navigate to your deployment space
   - Create AutoAI experiment or upload custom model
   - The UI guides you through feature engineering, model selection, and deployment

3. **Save the Deployment ID**:
   - Once deployment status shows _Deployed_, copy the **Deployment ID** (UUID format):

   ```
   a1b2c3d4-e5f6-7890-abcd-ef1234567890
   ```

   - Also note your **Space ID** from space settings page

---

### Step 2 - Download the Template

#### Option A: Using watsonx CLI (Recommended)

```bash
# Install CLI
pip install -U "ibm_watsonx_ai_cli>=0.5.0"

# Browse templates
watsonx-ai template new

# Select mcp-orchestrate-autoai-template-generic from the list
# Output: ✓ Template downloaded to ./mcp-orchestrate-autoai-template-generic

cd mcp-orchestrate-autoai-template-generic
```

#### Option B: Using Git Clone

```bash
git clone --no-tags --depth 1 --single-branch --filter=tree:0 --sparse \
  https://github.com/IBM/watsonx-developer-hub.git
cd watsonx-developer-hub
git sparse-checkout add agents/mcp/mcp-orchestrate-autoai-template-generic
cd agents/mcp/mcp-orchestrate-autoai-template-generic
```

#### Install Local Dependencies

```bash
pip install -r requirements-dev.txt
```

This installs:

- `ibm-watsonx-ai`: Connects to watsonx.ai for schema and scoring
- `python-dotenv`: Loads credentials from `.env`
- `pyyaml`: Writes generated `toolkit.yaml` and `agent.yaml`
- `ibm-watsonx-orchestrate`: CLI for managing agents and toolkits

---

### Step 3 - Configure the Environment

```bash
cp template.env .env
```

Edit `.env` with your credentials:

```bash
# .env
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_API_KEY=<your-ibm-cloud-iam-api-key>
WATSONX_SPACE_ID=<your-deployment-space-id>
WATSONX_AUTO_DEPLOYMENT_ID=<your-deployment-id>

# Optional: override LLM (default: groq/openai/gpt-oss-120b)
# LLM_NAME=groq/openai/gpt-oss-120b
```

| Variable                     | Where to find it                                                     |
| ---------------------------- | -------------------------------------------------------------------- |
| `WATSONX_URL`                | Region-specific endpoint (e.g., `https://us-south.ml.cloud.ibm.com`) |
| `WATSONX_API_KEY`            | IBM Cloud → Manage → Access (IAM) → API keys                         |
| `WATSONX_SPACE_ID`           | watsonx.ai → Deployment space → Manage tab                           |
| `WATSONX_AUTO_DEPLOYMENT_ID` | watsonx.ai → Deployments → select model                              |

> **Security:** Never commit `.env` to version control. The `.gitignore` already excludes it.

---

### Understanding the MCP Server Setup

Before deploying, let's clarify what the MCP server does and how you control it.

**MCP = Model Context Protocol** - an open standard that allows AI agents to safely call external tools.

#### How It Works

- **Local development:** MCP server runs as a Python process on your machine (`mcp_server/server.py`). You control all code.
- **Deployment:** `deploy.sh` packages the server and uploads to Orchestrate. Orchestrate manages execution.
- **Your role:** Provide credentials (API key, space ID, deployment ID). Generator auto-creates everything else.
- **Orchestrate's role:** Hosts agent, routes messages, calls MCP tool, formats responses.

#### Complete Flow

1. User asks question to Orchestrate agent
2. Agent evaluates what tool(s) to call
3. Agent calls `get_prediction` tool via MCP
4. MCP server validates inputs and calls watsonx.ai deployment
5. watsonx.ai returns prediction (e.g., risk score + confidence)
6. MCP server formats response
7. Agent generates human-readable response to user

> **Key point:** You don't manually deploy the MCP server. The `deploy.sh` script handles everything automatically.

---

### Step 4 - Generate Configs from Your Deployment

Generate `toolkit.yaml` and `agent.yaml` from your live deployment:

```bash
python scripts/generate_template.py
```

**Expected output:**

```
Connecting to watsonx.ai (us-south)...
Fetching deployment details for a1b2c3d4-e5f6-7890-abcd-ef1234567890...
✓ Found model asset: 11223344-aabb-ccdd-eeff-112233445566
Fetching model metadata...
✓ Input fields: tenure (integer), balance (double), ticket_count (integer)
✓ Label column: risk_score
Generated /path/to/toolkit.yaml
Generated /path/to/agent.yaml
```

#### What the script does internally

1. Loads `.env` credentials
2. Creates authenticated API client
3. Fetches deployment details to get model asset ID
4. Reads full model schema from repository
5. Extracts input fields and prediction column
6. Writes `toolkit.yaml` and `agent.yaml` with real field names

#### Generated `toolkit.yaml`

```yaml
spec_version: v1
kind: mcp
name: prediction-toolkit
description: Generic watsonx.ai model prediction toolkit
command: python server.py
env:
  - WATSONX_URL
  - WATSONX_API_KEY
  - WATSONX_SPACE_ID
  - WATSONX_AUTO_DEPLOYMENT_ID
tools:
  - "*"
package_root: ./mcp_server
```

#### Generated `agent.yaml` Example

```yaml
spec_version: v1
kind: native
name: autoai_prediction_agent
description: Predicts customer risk_score using a watsonx.ai deployed model.
llm: groq/openai/gpt-oss-120b
style: react
hide_reasoning: false
instructions: |
  You are a prediction assistant for customer risk scoring.

  STRICT RULES - follow these without exception:
  1. NEVER answer from your own knowledge.
  2. ALWAYS call get_prediction when all required fields provided.
  3. Ask only for missing fields, one at a time.
  4. After tool returns, report prediction clearly.
  5. Do NOT perform your own calculations.

  Required input fields:
       - tenure
       - balance
       - ticket_count
tools:
  - prediction-toolkit:get_prediction
collaborators: []
```

> **NOTE:** If your WML schema differs from expected (`entity.schemas.input[0].fields`, `entity.label_column`), adjust `_extract_input_fields()` and `_extract_label_column()` in `mcp_server/utils.py`.

---

### Step 5 - Set Up the watsonx Orchestrate CLI

The `ibm-watsonx-orchestrate` package was already installed. Now configure it.

#### Register your Orchestrate environment

```bash
orchestrate env add \
  -n my-orchestrate-env \
  -u https://<your-orchestrate-instance-url>
```

#### Authenticate

```bash
orchestrate env activate my-orchestrate-env \
  --api-key <your-orchestrate-api-key>
```

**Expected output:**

```
Activating environment: my-orchestrate-env
✓ Session token obtained. Token valid for 60 minutes.
✓ Active environment: my-orchestrate-env
```

> **Token expiry:** Tokens expire after 60 minutes. Re-run `orchestrate env activate` if deployment fails.

#### Verify

```bash
orchestrate connections list
```

---

### Step 6 - Deploy the Agent

Deploy everything with one command:

```bash
bash scripts/deploy.sh
```

This script:

1. Verifies authentication and `.env`
2. Generates fresh `toolkit.yaml` and `agent.yaml`
3. Loads environment variables
4. Creates connection in Orchestrate
5. Injects credentials into draft + live environments
6. Uploads MCP server package
7. Registers agent definition
8. Deploys agent to live

**Expected output:**

```
Starting deployment of prediction orchestration resources...
=========================================================

Pre-flight: Checking Orchestrate authentication...
✓ Orchestrate authentication OK

Step 1: Generating template files from deployment...
✓ Template files generated successfully
  - toolkit.yaml
  - agent.yaml

Step 2: Loading environment variables from .env...
✓ Environment variables loaded

Step 3: Adding connection 'prediction-connection'...
✓ Connection added successfully

Step 4: Configuring credentials for draft and live...
  [draft] Configuring...
  ✓ Connection configured for draft
  ✓ Credentials set for draft
  [live] Configuring...
  ✓ Connection configured for live
  ✓ Credentials set for live

Step 5: Importing toolkit...
✓ Toolkit imported successfully

Step 6: Importing agent...
✓ Agent imported successfully

Step 7: Deploying agent...
✓ Agent deployed successfully

=========================================================
✓ Deployment complete!

To run a conversation with the agent:
  orchestrate chat ask --agent-name autoai_prediction_agent --include-reasoning
```

**Verify deployment:**

```bash
orchestrate agents list
orchestrate toolkits list
orchestrate connections list
```

---

### Step 7 - Chat with Your Agent

```bash
orchestrate chat ask \
  --agent-name autoai_prediction_agent \
  --include-reasoning
```

The `--include-reasoning` flag shows agent's internal reasoning steps (useful for debugging).

#### Example Conversation

```
You: What is the risk score for a customer?

Agent: I need the following information to assess customer risk:
  - tenure (how many months as a customer)
  - balance (current account balance)
  - ticket_count (number of support tickets this month)

Please provide these values.

You: tenure=24, balance=15000, ticket_count=2

[Reasoning]
  All required fields provided.
  Calling tool: get_prediction({
    "tenure": 24,
    "balance": 15000,
    "ticket_count": 2
  })

[Tool response]
  { "prediction_column": "risk_score", "prediction": 0.35, "confidence": 0.92 }

Agent: Based on the prediction model:
  This customer has a risk score of 0.35 with 92% confidence.
  This is a low risk customer. No immediate action recommended.
```

✓ **End-to-end flow complete:** Agent collected details conversationally, called your model via MCP, received prediction, formatted response - all without hard-coded domain logic.

---

## Updating or Switching Models

Change your deployment in three steps:

1. **Update `.env`:**

   ```bash
   WATSONX_AUTO_DEPLOYMENT_ID=<new-deployment-id>
   ```

2. **Regenerate configs:**

   ```bash
   python scripts/generate_template.py
   ```

3. **Redeploy:**
   ```bash
   bash scripts/deploy.sh
   ```

> **Important:** The MCP server reads schema dynamically at startup. If you only update the deployment ID without regenerating YAMLs, the server works but agent instructions (listing required fields) will be outdated. Always regenerate when changing models.

---

## Running the MCP Server Locally

For testing and debugging before deployment:

```bash
pip install -r mcp_server/requirements.txt
cd mcp_server && python server.py
```

This starts the MCP server on stdio for local testing.

---

## Cleanup

Remove all Orchestrate resources and local artifacts:

```bash
./scripts/cleanup.sh
```

**Output:**

```
Starting cleanup of prediction orchestration resources...
==================================================

Pre-flight: Checking Orchestrate authentication...
✓ Orchestrate authentication OK

Step 1: Undeploying agent...
✓ Agent undeployed successfully

Step 2: Removing agent...
✓ Agent removed successfully

Step 3: Removing toolkit...
✓ Toolkit removed successfully

Step 4: Removing connection...
✓ Connection removed successfully

Step 5: Removing locally generated artifacts...
✓ Removed: toolkit.yaml agent.yaml

==================================================
✓ Cleanup complete!
```

> The cleanup script is idempotent - if resources were already removed manually, it skips with informational messages.

---

## Quick Reference - Full Command Sequence

```bash
# 1. Install CLI and get template
pip install -U "ibm_watsonx_ai_cli>=0.5.0"
watsonx-ai template new
cd mcp-orchestrate-autoai-template-generic

# 2. Install dependencies
pip install -r requirements-dev.txt

# 3. Configure
cp template.env .env
# Edit .env with your credentials

# 4. Setup Orchestrate
orchestrate env add -n my-env -u https://<orchestrate-url>
orchestrate env activate my-env --api-key <api-key>

# 5. Deploy
python scripts/generate_template.py
bash scripts/deploy.sh

# 6. Test
orchestrate chat ask --agent-name risk_prediction_agent --include-reasoning

# 7. Cleanup
bash scripts/cleanup.sh
```

---

## How the `get_prediction` Tool Works

1. At server startup, `utils._fetch_deployment_schema()` queries watsonx API for `INPUT_FIELDS` and `PREDICTION_COLUMN` (cached via `lru_cache`).
2. LLM collects all required fields from the user.
3. `server.py` validates them using dynamically built Pydantic model (`utils.create_input_model`).
4. `utils.build_scoring_payload` builds the WML scoring API format.
5. `api_client.deployments.score(...)` invokes the deployment.
6. `utils.extract_prediction` extracts result from response.
7. Returns `{"prediction_column": ..., "prediction": ...}`.

---

## Regeneration Cycle

Every time you change the deployment or refresh configs:

```bash
python scripts/generate_template.py
# Review toolkit.yaml / agent.yaml
./scripts/deploy.sh   # or manual import via orchestrate CLI
```

> The MCP server fetches schema dynamically at startup - just update `WATSONX_AUTO_DEPLOYMENT_ID` and restart the server. No regeneration needed for simple credential changes.

---

## Known Limitations

- **Feature importance:** Not currently generated or returned. Add separately if needed.
- **Unknown types:** Mapped to `str` by default. Verify for categorical columns.
- **Multi-output models:** Template optimized for single output column. Requires custom modifications to `mcp_server/utils.py` for multiple outputs.
