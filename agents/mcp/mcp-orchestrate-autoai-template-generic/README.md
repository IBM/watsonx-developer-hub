# Use watsonx AutoAI and MCP server with IBM watsonx Orchestrate (generic template).

Table of contents:  
* [Introduction](#introduction)  
* [AutoAI experiment](#autoai-experiment)  
* [Directory structure and files description](#directory-structure-and-files-description)  
* [Prerequisites](#prerequisites)  
* [Cloning and setting up the template](#cloning-and-setting-up-the-template)  
* [Configuring the environment](#configuring-the-environment)  
* [Generating configs](#generating-configs)  
* [Running the MCP server locally](#running-the-mcp-server-locally)  
* [Importing into Orchestrate](#importing-into-orchestrate)  
* [Cleanup](#cleanup)  
* [How the tool works](#how-the-get_autoai_prediction-tool-works)  
* [Regeneration cycle](#regeneration-cycle)  
* [Known limitations](#known-limitations)  


## Introduction

This template demonstrates how to build a generic IBM watsonx Orchestrate agent that exposes predictions from **any** deployed AutoAI model (watsonx.ai) as an MCP tool.

The MCP server fetches the model's input schema and target column **dynamically from the watsonx API at startup** — no hand-written config files are needed. `toolkit.yaml` and `agent.yaml` are build-time artifacts generated locally by `scripts/generate_template.py` based on the actual deployment.

## AutoAI experiment

This template works with **any** AutoAI experiment deployed in watsonx.ai. Deploy your experiment, then save the `deployment_id` of the deployed model — it will be required in the `.env` file.

Sample AutoAI experiment notebooks are available in the [watsonx-ai-samples repository](https://github.com/IBM/watsonx-ai-samples/tree/master/cloud/notebooks/python_sdk/experiments/autoai).

## Directory structure and files description

```
mcp-orchestrate-autoai-template-generic
 ┣ LICENSE
 ┣ README.md
 ┣ template.env
 ┣ .gitignore
 ┣ requirements-dev.txt
 ┣ scripts/
 ┃  ┣ generate_template.py
 ┃  ┣ deploy.sh
 ┃  ┗ cleanup.sh
 ┣ mcp_server/
 ┃  ┣ server.py
 ┃  ┣ utils.py
 ┃  ┗ requirements.txt
 ┣ toolkit.yaml              ← GENERATED, gitignored
 ┗ agent.yaml                ← GENERATED, gitignored
```

Notable files:
- `template.env`: Template file with placeholders for the required environment variables.
- `requirements-dev.txt`: Local dependencies used by the generator script and the Orchestrate CLI.
- `scripts/generate_template.py`: Queries watsonx.ai, then writes `toolkit.yaml` and `agent.yaml`.
- `scripts/deploy.sh`: Runs the generator and imports the configs into Orchestrate in one step.
- `scripts/cleanup.sh`: Removes the agent, toolkit, and connection from Orchestrate and deletes local artifacts.
- `mcp_server/server.py`: MCP server — defines the `get_autoai_prediction` tool.
- `mcp_server/utils.py`: Scoring helpers, dynamic schema fetching, and Pydantic model construction.
- `mcp_server/requirements.txt`: Runtime dependencies (only what `server.py` needs).

## Prerequisites

- Python 3.10 or higher
- Access to IBM watsonx.ai
- Existing AutoAI deployment
- IBM watsonx Orchestrate instance
- Required Python packages (see [Configuring the environment](#configuring-the-environment))

## Cloning and setting up the template

In order not to clone the whole `IBM/watsonx-developer-hub` repository we'll use git's shallow and sparse cloning feature to checkout only the template's directory:

```sh
git clone --no-tags --depth 1 --single-branch --filter=tree:0 --sparse https://github.com/IBM/watsonx-developer-hub.git
cd watsonx-developer-hub
git sparse-checkout add agents/mcp/mcp-orchestrate-autoai-template-generic
```

Move to the directory with the template:

```sh
cd agents/mcp/mcp-orchestrate-autoai-template-generic
```

> [!NOTE]
> From now on it'll be considered that the working directory is `watsonx-developer-hub/agents/mcp/mcp-orchestrate-autoai-template-generic/`

Install local dependencies:

```sh
pip install -r requirements-dev.txt
```

> `mcp_server/requirements.txt` is installed separately only if you want to run the MCP server locally for testing — see [Running the MCP server locally](#running-the-mcp-server-locally).

## Configuring the environment

Copy the template file:

```sh
cp template.env .env
```

Fill in `.env` with your actual values:

```sh
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_API_KEY=your_api_key
WATSONX_SPACE_ID=your_space_id
WATSONX_AUTOAI_DEPLOYMENT_ID=your_autoai_deployment_id
```

## Generating configs

Run the generator script:

```sh
python scripts/generate_template.py
```

The script:
1. Loads `.env`.
2. Connects to watsonx.ai (`APIClient`).
3. Fetches deployment details (`deployments.get_details`).
4. Reads `entity.asset.id` — the model ID in the repository.
5. Fetches model metadata via `repository.get_model_details()`.
6. Extracts the input schema and `label_column`.
7. Writes `toolkit.yaml` and `agent.yaml`.

> [!NOTE]
> If the response structure of your WML instance differs from the expected one (`entity.schemas.input[0].fields`, `entity.label_column`), the script will raise a readable error instead of a raw `KeyError`. Dump `asset_details` to JSON and adjust `_extract_input_fields()` / `_extract_label_column()` in `mcp_server/utils.py`.

## Running the MCP server locally

To start the MCP server locally, install the runtime dependencies and execute:

```sh
pip install -r mcp_server/requirements.txt
cd mcp_server && python server.py
```

## Importing into Orchestrate

To generate configs and import everything into Orchestrate in one step, execute:

```sh
./scripts/deploy.sh
```

This script runs the generator (step equivalent to [Generating configs](#generating-configs)) and additionally:
- Creates and configures the `autoai-prediction-connection` (draft + live).
- Imports `toolkit.yaml` and `agent.yaml`.
- Deploys the agent.

## Cleanup

To remove all Orchestrate resources and local artifacts, execute:

```sh
./scripts/cleanup.sh
```

This removes the agent, toolkit, and connection from Orchestrate along with local `toolkit.yaml` and `agent.yaml` files.

## How the `get_autoai_prediction` tool works

1. At server startup `utils._fetch_deployment_schema()` queries the watsonx API and retrieves `INPUT_FIELDS` and `PREDICTION_COLUMN`. The result is cached (`lru_cache`) — the API is queried only once per process lifetime.
2. The LLM collects all fields from `INPUT_FIELDS` from the user.
3. `server.py` validates them using a dynamically built Pydantic model (`utils.create_input_model`).
4. `utils.build_scoring_payload` builds the payload in the WML scoring API format.
5. `api_client.deployments.score(...)` invokes the deployment.
6. `utils.extract_prediction` extracts the result from the response.
7. Returns `{"prediction_column": ..., "prediction": ...}`.

## Regeneration cycle

Every time you change the deployment or want to refresh `toolkit.yaml`/`agent.yaml`:

```sh
python scripts/generate_template.py
# review toolkit.yaml / agent.yaml
./scripts/deploy.sh   # or manual import via `orchestrate toolkits/agents import`
```

> `mcp_server/utils.py` fetches the model schema dynamically at startup — just update `WATSONX_AUTOAI_DEPLOYMENT_ID` and restart the server, no file regeneration needed.

## Known limitations

- Feature importance is **not** currently generated or returned. If you need it in the agent response, it must be added separately.
- `python_type_for_field` maps unknown types to `str` — for categorical columns (`type: "other"`, such as `species`) this is intentional behaviour, but it is worth verifying consciously for other datasets.
