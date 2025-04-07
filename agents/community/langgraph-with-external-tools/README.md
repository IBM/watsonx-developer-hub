# LangGraph LLM Template with External Tool Integration  

Table of contents:  
* [Introduction](#introduction)  
* [Setting up Secrets Manager](#setting-up-secrets-manager)  
* [Directory structure and file descriptions](#directory-structure-and-file-descriptions)  
* [Prerequisites](#prerequisites)  
* [Cloning and setting up the template](#cloning-and-setting-up-the-template)  
* [Modifying and configuring the template](#modifying-and-configuring-the-template)  
* [Running unit tests for the template](#running-unit-tests-for-the-template)  
* [Running the application locally](#running-the-application-locally)  
* [Deploying on Cloud](#deploying-on-ibm-cloud)  
* [Inferencing the deployment](#inferencing-the-deployment)  


## Introduction  

This repository provides a foundational template for developing Large Language Model (LLM) applications using the LangGraph framework. It facilitates seamless deployment as an AI service within IBM watsonx.ai on IBM Cloud[^1]. The template includes support for integrating external tools and services, with secure credential management handled via a secret manager.  
An AI service is a deployable unit of code that captures the logic of your generative AI use case. For an in-depth description of the topic, please refer to the [IBM watsonx.ai documentation](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ai-services-templates.html?context=wx&audience=wdp).  

The template builds a simple application with external tool for addressing Web Search Agent use case.  

[^1]: _IBM watsonx.ai for IBM Cloud_ is a full and proper name of the component we're using in this template and only a part of the whole suite of products offered in the SaaS model within IBM Cloud environment. Throughout this README, for the sake of simplicity, we'll be calling it just an **IBM Cloud**.  


## Setting up Secrets Manager

This section describes how to securely configure and store API credentials using IBM Cloud® Secrets Manager so they can be retrieved at runtime by the application. This approach eliminates the need to store sensitive data in source code or configuration files.  

#### Install the required package  

```sh
pip install ibm-watsonx-ai
pip install ibm-secrets-manager-sdk
```

#### Create a `BearerTokenAuthenticator` object using the token from the APIClient  

```python
from ibm_watsonx_ai import APIClient
from ibm_cloud_sdk_core.authenticators import BearerTokenAuthenticator

client = APIClient(...)
authenticator = BearerTokenAuthenticator(client.token)
```

#### Initialize the Secrets Manager client  

```python
from ibm_secrets_manager_sdk.secrets_manager_v2 import SecretsManagerV2

secretsManager = SecretsManagerV2(authenticator=authenticator)
```

#### Set the Secrets Manager service URL  

```python
secretsManager.set_service_url(service_url="<YOUR_SECRETS_MANAGER_SERVICE_URL>")
```
You must also specify this URL in the `config.toml` file under the `service_manager_service_url` key:

```toml
[deployment.online.parameters]
# Secret Manager configuration
# Required:
service_manager_service_url = "<YOUR_SECRETS_MANAGER_SERVICE_URL>"
```

> [!NOTE]
>For details on how to construct the correct service URL based on your region, refer to the [IBM Secrets Manager API documentation – Endpoints section](https://cloud.ibm.com/apidocs/secrets-manager/secrets-manager-v2#endpoints).

#### Create and store the secret  

Below is an example of a Key-Value (KV) secret containing a dummy Tavily API key:  
```python
secret_prototype_model = {
    'secret_type': 'kv',
    'secret_group_id': 'default',
    'labels': ['dev', 'us-south'],
    'name': 'tavily_apikey',
    'description': 'Description of my tavily secret.',
    'data': {"tavily_api_key": "dummy_tavily_api_key"},
    'custom_metadata': {'metadata_custom_key': 'metadata_custom_value'},
    'version_custom_metadata': {'custom_version_key': 'custom_version_value'},
}

response = secretsManager.create_secret(secret_prototype=secret_prototype_model)
```

> [!WARNING]  
> Ensure the format of the secret matches the expected schema in the codebase, especially under the `data` key, as used in the `tools.py` file.

#### Retrieve and configure the `secret_id`  

The response from the create_secret call contains the ID of the created secret:
```python
secret_id = response.result['id']
print(secret_id)
```

Copy this `secret_id` and update your `config.toml` file under the `secret_id` key:
```toml
[deployment.online.parameters]
# Secret Manager configuration
# Required:
secret_id = "<YOUR_SECRET_ID>"
```

Once configured, your application will securely fetch the API key from Secrets Manager at runtime and use it to initialize external tools like TavilySearch.

## Directory structure and file descriptions  

The high level structure of the repository is as follows:  

langgraph-with-external-tools  
 ┣ src  
 ┃ ┗ langgraph_with_external_tools  
 ┃   ┣ agent.py  
 ┃   ┗ tools.py  
 ┣ schema  
 ┣ ai_service.py  
 ┣ config.toml.example  
 ┣ pyproject.toml  

- `langgraph-with-external-tools` folder: Contains auxiliary files used by the deployed function. They provide various framework specific definitions and extensions. This folder is packaged and sent to IBM Cloud during deployment as a [package extension](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ml-create-custom-software-spec.html?context=wx&audience=wdp#custom-wml).  
- `schema` folder: Contains request and response schemas for the `/ai_service` endpoint queries.  
- `ai_service.py` file: Contains the function to be deployed as an AI service defining the application's logic  
- `config.toml.example` file: A configuration file with placeholders that stores the deployment metadata. After downloading the template repository, copy the contents of the `config.toml.example` file to the `config.toml` file and fill in the required fields. `config.toml` file can also be used to tweak the model for your use case. 

## Prerequisites  

- [Poetry](https://python-poetry.org/) package manager,  
- [Pipx](https://github.com/pypa/pipx) due to Poetry's recommended [installation procedure](https://python-poetry.org/docs/#installation)  


## Cloning and setting up the template locally  


### Step 1: Clone the repository  

In order not to clone the whole `IBM/watsonx-developer-hub` repository we'll use git's shallow and sparse cloning feature to checkout only the template's directory:  

```sh
git clone --no-tags --depth 1 --single-branch --filter=tree:0 --sparse https://github.com/IBM/watsonx-developer-hub.git
cd watsonx-developer-hub
git sparse-checkout add agents/community/langgraph-with-external-tools
```  

Move to the directory with the agent template:

```sh
cd agents/community/langgraph-with-external-tools
```

> [!NOTE]
> From now on it'll be considered that the working directory is `watsonx-developer-hub/agents/community/langgraph-with-external-tools`  


### Step 2: Install poetry  

```sh
pipx install --python 3.11 poetry
```

### Step 3: Install the template  

Running the below commands will install the repository in a separate virtual environment  

```sh
poetry install
```

### Step 4 (OPTIONAL): Activate the virtual environment  

```sh
source $(poetry -q env use 3.11 && poetry env info --path)/bin/activate
```

### Step 5: Export PYTHONPATH  

Adding working directory to PYTHONPATH is necessary for the next steps. In your terminal execute:  
```sh
export PYTHONPATH=$(pwd):${PYTHONPATH}
```

## Modifying and configuring the template  

[config.toml](config.toml) file should be filled in before either deploying the template on IBM Cloud or executing it locally.  
Possible config parameters are given in the provided file and explained using comments (when necessary).  


The template can also be extended to provide additional key-value data to the application. Create a special asset from within your deployment space called _Parameter Sets_. Use the _watsonx.ai_ library to instantiate it and later reference it from the code.  
For detailed description and API please refer to the [IBM watsonx.ai Parameter Set's docs](https://ibm.github.io/watsonx-ai-python-sdk/core_api.html#parameter-sets)  


Sensitive data should not be passed unencrypted, e.g. in the configuration file. The recommended way to handle them is to make use of the [IBM Cloud® Secrets Manager](https://cloud.ibm.com/apidocs/secrets-manager/secrets-manager-v2). The approach to integrating the Secrets Manager's API with the app is for the user to decide on.  


The [agent.py](src/langgraph/agent.py) file builds app the graph consisting of nodes and edges. The former define the logic for agents while the latter control the logic flow in the whole graph.  
For detailed info on how to modify the graph object please refer to [LangGraph's official docs](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/#create-graph)  


The [ai_service.py](ai_service.py) file encompasses the core logic of the app alongside the way of authenticating the user to the IBM Cloud.  
For a detailed breakdown of the ai-service's implementation please refer the [IBM Cloud docs](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ai-services-create.html?context=wx)  


[tools.py](src/langgraph_with_external_tools/tools.py) file stores the definition for tools enhancing the chat model's capabilities.  
In order to add new tool create a new function, wrap it with the `@tool` decorator and add to the `TOOLS` list in the `extensions` module's [__init__.py](src/langgraph_with_external_tools/__init__.py)

For more sophisticated use cases (like async tools), please refer to the [langchain docs](https://python.langchain.com/docs/how_to/custom_tools/#creating-tools-from-runnables).  

## Testing the template  

The `tests/` directory's structure resembles the repository. Adding new tests should follow this convention.  
For exemplary purposes only the tools and some general utility functions are covered with unit tests.  

Running the below command will run the complete tests suite:
```sh
pytest -r 'fEsxX' tests/
```  

## Running the application locally  

It is possible to run (or even debug) the ai-service locally, however it still requires creating the connection to the IBM Cloud.  

### Step 1: Fill in the `config` file  

Enter the necessary credentials in the `config.toml` file.  

### Step 2: Run the script for local AI service execution  

```sh
python examples/execute_ai_service_locally.py
```  

### Step 3: Ask the model  

Choose from some pre-defined questions or ask the model your own.


## Deploying on IBM Cloud  

Follow these steps to deploy the model on IBM Cloud.  

### Step 1: Fill in the `config` file  

Enter the necessary credentials in the `config.toml` file.  

### Step 2: Run the deployment script  

```sh
python scripts/deploy.py
```  

Successfully completed script will print on stdout the `deployment_id` which is necessary to locally test the deployment. For further info please refer [to the next section](#querying-the-deployment)  

## Querying the deployment  

Follow these steps to inference your deployment. The [query_existing_deployment.py](examples/query_existing_deployment.py) file shows how to test the existing deployment using `watsonx.ai` library.  

### Step 1: Initialize the deployment ID  

Initialize the `deployment_id` variable in the [query_existing_deployment.py](examples/query_existing_deployment.py) file.  
The _deployment_id_ of your deployment can be obtained from [the previous section](#deploying-on-ibm-cloud) by running [scripts/deploy.sh](scripts/deploy.py)  

### Step 2: Run the script for querying the deployment  

```sh
python examples/query_existing_deployment.py
```   
