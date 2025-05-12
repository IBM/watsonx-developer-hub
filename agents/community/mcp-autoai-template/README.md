# Use watsonx, and MCP server to invoke on AutoAI deployment.

Table of contents:  
* [Introduction](#introduction)  
* [AutoAI experiemnt](#autoai_experiemnt)  
* [Directory structure and files description](#directory-structure-and-files-description)  
* [Prerequisites](#prerequisites)  
* [Cloning and setting up the template](#cloning-and-setting-up-the-template)  
* [Configuring the environment](#configuring-the-environment)  
* [Running the MCP Server Locally](#running-the-mcp-server-locally)  
* [Testing the MCP Server Locally](#testing-the-mcp-server-locally)  


## Introduction  

This project demonstrates how to build an AI application using IBM watsonx, LangChain, and MCP Server to interact with a deployed AutoAI model.

It takes free-form text describing a person, uses a foundation model hosted on IBM watsonx to extract structured information, and then invokes an AutoAI deployment that predicts credit risk based on those structured inputs.

## AutoAI experiemnt

Before starting work with the MCP server, please review the notebook [Use AutoAI and Lale to predict credit risk with ibm-watsonx-ai](https://github.com/IBM/watsonx-ai-samples/blob/master/cloud/notebooks/python_sdk/experiments/autoai/Use%20AutoAI%20and%20Lale%20to%20predict%20credit%20risk.ipynb) to perform the deployment, which will later be used as a tool agent.

This notebook guides you through:

- Uploading and exploring the credit risk dataset
- Running an AutoAI experiment to train a model
- Deploying the trained model into your IBM watsonx space

> Once deployed, copy the deployment ID and add it to your .env file — it will be used by the MCP server to make predictions.

## Directory structure and files description

mcp-autoai-template
 ┣ mcp_server.py          # Main MCP server with tools (including AutoAI invocation)
 ┣ interact_with_mcp.py   # Script for sending sample queries to the running MCP server for testing purposes
 ┣ utils.py               # Helper functions for authentication, formatting, and client setup
 ┣ template.env           # Template file for environment variable configuration
 ┗ README.md              # This README

Notable files:
- `mcp_server.py`: Starts a FastMCP server and defines tools like invoke_credit_risk_deployment.
- `interact_with_mcp.py`: Sends a sample request to the running MCP server to test tool invocation and validate the server response.
- `utils.py`: Contains helper functions for setting up watsonx client, formatting payloads, and loading config.
- `template.env`: Template file with placeholders for environment variables.

## Prerequisites

- Python 3.10 or higher
- Access to IBM watsonx.ai
- Existing AutoAI deployment
- Required Python packages

You can install the dependencies individually:
```sh
pip install langchain-ibm
pip install langchain
pip install langgraph
pip install python-dotenv
pip install mcp
pip install langchain_mcp_adapters
```
Alternatively, you can install all dependencies at once using the `requirements.txt` file:
```sh
pip install -r requirements.txt
```

## Cloning and setting up the template

In order not to clone the whole `IBM/watsonx-developer-hub` repository we'll use git's shallow and sparse cloning feature to checkout only the template's directory:  

```sh
git clone --no-tags --depth 1 --single-branch --filter=tree:0 --sparse https://github.com/IBM/watsonx-developer-hub.git
cd watsonx-developer-hub
git sparse-checkout add community/mcp-autoai-template
```  

Move to the directory with the mcp autoai template:

```sh
cd community/mcp-autoai-template
```

> [!NOTE]
> From now on it'll be considered that the working directory is `watsonx-developer-hub/community/mcp-autoai-template/` 

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

## Running the MCP Server Locally

To start the MCP server locally, execute the following command:

```sh
python mcp_server.py
```

This will launch the FastMCP server and register the necessary tools.

## Testing the MCP Server Locally

To test the MCP server, open a new terminal while the server is running and execute the following command:

```sh
python interact_with_mcp.py  
```
