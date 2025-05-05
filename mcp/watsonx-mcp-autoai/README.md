# Use watsonx, and MCP server to invoke on AutoAI deployment.

Table of contents:  
* [Introduction](#introduction)  
* [AutoAi experiemnt](#autoai_experiemnt)  
* [Directory structure and file descriptions](#directory-structure-and-file-descriptions)  
* [Prerequisites](#prerequisites)  
* [Cloning and setting up the template](#cloning-and-setting-up-the-template)  
* [Configuring the environment](#configuring-the-environment)  
* [Running the application locally](#running-the-application-locally)  


## Introduction  

This project demonstrates how to build an AI application using IBM watsonx, LangChain, and MCP Server to interact with a deployed AutoAI model.

It takes free-form text describing a person, uses a foundation model hosted on IBM watsonx to extract structured information, and then invokes an AutoAI deployment that predicts credit risk based on those structured inputs.

## AutoAi experiemnt

Before starting work with the MCP server, please review the notebook [Use AutoAI and Lale to predict credit risk with ibm-watsonx-ai](https://github.com/IBM/watsonx-ai-samples/blob/master/cloud/notebooks/python_sdk/experiments/autoai/Use%20AutoAI%20and%20Lale%20to%20predict%20credit%20risk.ipynb) to perform the deployment, which will later be used as a tool agent.

This notebook guides you through:

- Uploading and exploring the credit risk dataset
- Running an AutoAI experiment to train a model
- Deploying the trained model into your IBM watsonx space

> Once deployed, copy the deployment ID and add it to your .env file — it will be used by the MCP server to make predictions.

## Directory structure and file descriptions

watsonx-mcp-autoai
 ┣ mcp_server.py                                                      # Main MCP server with tools (including AutoAI invocation)
 ┣ Use watsonx, and MCP server to invoke on AutoAI deployment.ipynb   # Notebook with example usage and explanation
 ┣ utils.py                                                           # Helper functions for authentication, formatting, and client setup
 ┣ template.env                                                       # Template file for environment variable configuration
 ┗ README.md                                                          # This README

Notable files:
- `mcp_server.py`: Starts a FastMCP server and defines tools like invoke_credit_risk_deployemnt.
- `Use watsonx, and MCP server to invoke on AutoAI deployment.ipynb`: A reference notebook showing how the components work together interactively.
- `utils.py`: Contains helper functions for setting up watsonx client, formatting payloads, and loading config.
- `template.env`: Template file with placeholders for environment variables.

## Prerequisites

- Python 3.10+
- Access to IBM watsonx.ai
- AutoAI deployment already created
- Required packages

```sh
%pip install langchain-ibm
%pip install langchain
%pip install langgraph
%pip install python-dotenv
%pip install mcp
%pip install langchain_mcp_adapters
```

## Cloning and setting up the template

In order not to clone the whole `IBM/watsonx-developer-hub` repository we'll use git's shallow and sparse cloning feature to checkout only the template's directory:  

```sh
git clone --no-tags --depth 1 --single-branch --filter=tree:0 --sparse https://github.com/IBM/watsonx-developer-hub.git
cd watsonx-developer-hub
git sparse-checkout add mcp/watsonx-mcp-autoai
```  

Move to the directory with the mcp autoai template:

```sh
cd mcp/watsonx-mcp-autoai
```

> [!NOTE]
> From now on it'll be considered that the working directory is `watsonx-developer-hub/mcp/watsonx-mcp-autoai/` 

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

WATSONX_MODEL_ID="mistralai/mistral-large"
WATSONX_CREDIT_RISK_DEPLOYMENT_ID=your_autoai_deployment_id
```

## Running the application locally

Run the MCP server with:

```sh
python mcp_server.py
```

This starts a FastMCP server that registers tools.

