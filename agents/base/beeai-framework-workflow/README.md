# A Base beeai-framework LLM app template with function calling capabilities  

Table of contents:  
* [Introduction](#introduction)  
* [Directory structure and file descriptions](#directory-structure-and-file-descriptions)  
* [Prerequisites](#prerequisites)  
* [Cloning and setting up the template](#cloning-and-setting-up-the-template)  
* [Modifying and configuring the template](#modifying-and-configuring-the-template)  
* [Running unit tests for the template](#running-unit-tests-for-the-template)  
* [Running the application locally](#running-the-application-locally)  
* [Deploying on Cloud](#deploying-on-ibm-cloud)  
* [Inferencing the deployment](#inferencing-the-deployment)  


## Introduction  

This repository provides a basic template for LLM apps built using the beeai-framework. It also makes it easy to deploy them as an AI service as part of IBM watsonx.ai for IBM Cloud[^1].  
An AI service is a deployable unit of code that captures the logic of your generative AI use case. For and in-depth description of the topic please refer to the [IBM watsonx.ai documentation](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ai-services-templates.html?context=wx&audience=wdp).  

[^1]: _IBM watsonx.ai for IBM Cloud_ is a full and proper name of the component we're using in this template and only a part of the whole suite of products offered in the SaaS model within IBM Cloud environment. Throughout this README, for the sake of simplicity, we'll be calling it just an **IBM Cloud**.  

The template builds a simple multi agent workflow use case.

Streaming version coming soon to this template.

## Directory structure and file descriptions  

The high level structure of the repository is as follows:  

beeai-framework-workflow  
 ┣ src  
 ┃ ┗ beeai_framework_workflow_base  
 ┃   ┣ workflow.py  
 ┣ schema  
 ┣ ai_service.py  
 ┣ config.toml.example  
 ┣ pyproject.toml  

- `beeai_framework_workflow_base` folder: Contains auxiliary files used by the deployed function. They provide various framework specific definitions and extensions. This folder is packaged and sent to IBM Cloud during deployment as a [package extension](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ml-create-custom-software-spec.html?context=wx&audience=wdp#custom-wml).  
- `schema` folder: Contains request and response schemas for the `/ai_service` endpoint queries.  
- `ai_service.py` file: Contains the function to be deployed as an AI service defining the application's logic  
- `config.toml.example` file: A configuration file with placeholders that stores the deployment metadata. After downloading the template repository, copy the contents of the config.toml.example file to the config.toml file and fill in the required fields. config.toml file can also be used to tweak the model for your use case.

## Prerequisites  

- [Poetry](https://python-poetry.org/) package manager,  
- [Pipx](https://github.com/pypa/pipx) due to Poetry's recommended [installation procedure](https://python-poetry.org/docs/#installation)  


## Cloning and setting up the template locally  


### Step 1: Clone the repository  

In order not to clone the whole `IBM/watsonx-developer-hub` repository we'll use git's shallow and sparse cloning feature to checkout only the template's directory:  

```sh
git clone --no-tags --depth 1 --single-branch --filter=tree:0 --sparse https://github.com/IBM/watsonx-developer-hub.git
cd watsonx-developer-hub
git sparse-checkout add agents/base/beeai-framework-workflow
```  

Move to the directory with the agent template:

```sh
cd agents/base/beeai-framework-workflow/
```

> [!NOTE]
> From now on it'll be considered that the working directory is `watsonx-developer-hub/agents/base/beeai-framework-workflow/`  


### Step 2: Install poetry  

```sh
pipx install --python 3.11 poetry
```

### Step 3: Install the template    

Running the below commands will install the repository in a separate virtual environment  

```sh
poetry install --with dev
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


The [workflow.py](src/beeai_framework_workflow_base/workflow.py) file creates workflows and prompts.
For detailed info on how to modify the workflow please refer to [beeai-framework's official documentation](https://github.com/i-am-bee/beeai-framework)  


The [ai_service.py](ai_service.py) file encompasses the core logic of the app alongside the way of authenticating the user to the IBM Cloud.  
For a detailed breakdown of the ai-service's implementation please refer the [IBM Cloud docs](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ai-services-create.html?context=wx)  

For more sophisticated use cases, please refer to the [beeai-framework docs](https://github.com/i-am-bee/beeai-framework).  

## Running the application locally  

It is possible to run (or even debug) the ai-service locally, however it still requires creating the connection to the IBM Cloud.  

### Step 1: Fill in the `config` file  

Enter the necessary credentials in the `config.toml` file.  

### Step 2: Run the script for local AI service execution  

```sh
python examples/execute_ai_service_locally.py
```  

### Step 3: Ask the model  

Choose from some pre-defined location or enter one of your own.


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
