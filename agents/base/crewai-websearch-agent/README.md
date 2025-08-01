# A Base CrewAI LLM app template with function calling capabilities 🚀

## 📖 Table of Contents
* [Introduction](#-introduction)  
* [Directory structure and file descriptions](#-directory-structure-and-file-descriptions)  
* [Prerequisites](#-prerequisites)  
* [Installation](#-installation)
* [Configuration](#%EF%B8%8F-configuration)  
* [Modifying and configuring the template](#-modifying-and-configuring-the-template)  
* [Testing the template](#-testing-the-template)  
* [Running the application locally](#-running-the-application-locally)  
* [Deploying on IBM Cloud](#%EF%B8%8F-deploying-on-ibm-cloud)  
* [Querying the deployment](#-querying-the-deployment)  
* [Running the graphical app locally](#%EF%B8%8F-running-the-graphical-app-locally) 
* [Cloning template (Optional)](#-cloning-template-optional)  

## 🤔 Introduction

This repository provides a basic template for LLM apps built using CrewAI framework. It also makes it easy to deploy them as an AI service as part of IBM watsonx.ai for IBM Cloud[^1].

An AI service is a deployable unit of code that encapsulates the logic of your generative AI use case. For an in-depth description of AI services, please refer to the [IBM watsonx.ai documentation](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ai-services-templates.html?context=wx&audience=wdp).

[^1]: _IBM watsonx.ai for IBM Cloud_ is a full and proper name of the component we're using in this template and only a part of the whole suite of products offered in the SaaS model within IBM Cloud environment. Throughout this README, for the sake of simplicity, we'll be calling it just an **IBM Cloud**.

**Highlights:**

* 🚀 Easy-to-extend agent and tool modules
* ⚙️ Configurable via `config.toml`
* 🌐 Step-by-step local and cloud deployment

## 🗂 Directory structure and file descriptions

The high level structure of the repository is as follows:  

```
crewai-websearch-agent/
├── src/
│   └── crewai_web_search/
│       ├── crew.py
│       ├── tools/
│       └── config/
├── schema/
├── ai_service.py
├── config.toml.example
└── pyproject.toml
```

* **`crewai_web_search`** folder: Contains CrewAI agents configuration yaml files (`src/crewai_web_search/config`) and auxiliary files used by the deployed function. These files provide various framework specific definitions and extensions. This folder is packaged and sent to IBM Cloud during deployment as a [package extension](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ml-create-custom-software-spec.html?context=wx&audience=wdp#custom-wml).  
* **`schema`** folder: Contains request and response schemas for the `/ai_service` endpoint queries.  
* **`ai_service.py`** file: Contains the function to be deployed as an AI service defining the application's logic  
* **`config.toml.example`** file: A configuration file with placeholders that stores the deployment metadata. After downloading the template repository, copy the contents of the `config.toml.example` file to the `config.toml` file and fill in the required fields. `config.toml` file can also be used to tweak the model for your use case.

## 🛠 Prerequisites

* **Python 3.11**
* **[Poetry](https://python-poetry.org/)** package manager (install via [pipx](https://github.com/pypa/pipx))
* IBM Cloud access and permissions 

## 📥 Installation

To begin working with this template using the Command Line Interface (CLI), please ensure that the IBM watsonx AI CLI tool is installed on your system. You can install or upgrade it using the following command:

1. **Install CLI**:

   ```sh
   pip install -U ibm-watsonx-ai-cli
   ```

2. **Download template**:
   ```sh
   watsonx-ai template new "base/crewai-websearch-agent"
   ```

   Upon executing the above command, a prompt will appear requesting the user to specify the target directory for downloading the template. Once the template has been successfully downloaded, navigate to the designated template folder to proceed.

> [!NOTE]
> Alternatively, it is possible to set up the template using a different method. For detailed instructions, please refer to the section "[Cloning template (Optional)](#-cloning-template-optional)".

3. **Install Poetry**:

   ```sh
   pipx install --python 3.11 poetry
   ```

4. **Install the template**:

    Running the below commands will install the repository with dev environment in a separate virtual environment
   
   ```sh
   poetry install --with dev
   ```

5. **(Optional) Activate the virtual environment**:

   ```sh
   source $(poetry -q env use 3.11 && poetry env info --path)/bin/activate
   ```

6. **Export PYTHONPATH**:

   Adding working directory to PYTHONPATH is necessary for the next steps.

   ```sh
   export PYTHONPATH=$(pwd):${PYTHONPATH}
   ```

## ⚙️ Configuration

1. Copy `config.toml.example` → `config.toml`.
2. Fill in IBM Cloud credentials.

## 🎨 Modifying and configuring the template 

[config.toml](config.toml) file should be filled in before either deploying the template on IBM Cloud or executing it locally.  
Possible config parameters are given in the provided file and explained using comments (when necessary).  


The template can also be extended to provide additional key-value data to the application. Create a special asset from within your deployment space called _Parameter Sets_. Use the _watsonx.ai_ library to instantiate it and later reference it from the code.  
For detailed description and API please refer to the [IBM watsonx.ai Parameter Set's docs](https://ibm.github.io/watsonx-ai-python-sdk/core_api.html#parameter-sets)  


Sensitive data should not be passed unencrypted, e.g. in the configuration file. The recommended way to handle them is to make use of the [IBM Cloud® Secrets Manager](https://cloud.ibm.com/apidocs/secrets-manager/secrets-manager-v2). The approach to integrating the Secrets Manager's API with the app is for the user to decide on.  


The [crew.py](src/crewai_web_search/crew.py) creates an AI crew, which consists of agents and their tasks.
For detailed info on how to modify the crew object please refer to [CrewAI's official docs](https://docs.crewai.com/quickstart)  


The [ai_service.py](ai_service.py) file encompasses the core logic of the app alongside the way of authenticating the user to the IBM Cloud.  
For a detailed breakdown of the ai-service's implementation please refer the [IBM Cloud docs](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ai-services-create.html?context=wx)  


[tools.py](src/crewai_web_search/tools/tools.py) file stores the definition for tools enhancing the chat model's capabilities.  
To add a new tool, create a class that extends the `crewai.tools.BaseTool` base class and has a `_run` method defined.

## 🧪 Testing the template

The `tests/` directory's structure resembles the repository. Adding new tests should follow this convention.  
For exemplary purposes only the tools and some general utility functions are covered with unit tests.  

Running the below command will run the complete tests suite:
```sh
pytest -r 'fEsxX' tests/
```  

## 💻 Running the application locally

It is possible to run (or even debug) the ai-service locally, however it still requires creating the connection to the IBM Cloud.

Ensure `config.toml` is configured.

You can test and debug your AI service locally via two alternative flows:

### ✅ Recommended flow: CLI

```sh
watsonx-ai template invoke "<PROMPT>"
```

### ⚠️ Alternative flow: Python Script (Deprecated)

1. **Run Python Script**:

   ```sh
   python examples/execute_ai_service_locally.py
   ```

2. **Ask the model**:

   Choose from some pre-defined questions or ask the model your own.

> [!WARNING]  
> This flow is deprecated and will be removed in a future release. Please migrate to recommended flow as soon as possible.

## ☁️ Deploying on IBM Cloud

Follow these steps to deploy the model on IBM Cloud. 

Ensure `config.toml` is configured.

You can deploy your AI service to IBM Cloud via two alternative flows:

### ✅ Recommended flow: CLI

```sh
watsonx-ai service new
```

*Config file updates automatically with `deployment_id`.*

### ⚠️ Alternative flow: Python Script (Deprecated)

```sh
python scripts/deploy.py
```

*Script prints `deployment_id`; update `config.toml`.*

> [!WARNING]  
> This flow is deprecated and will be removed in a future release. Please migrate to recommended flow as soon as possible.

## 🔍 Querying the deployment

You can send inference requests to your deployed AI service via two alternative flows:

### ✅ Recommended flow: CLI

```sh
watsonx-ai service invoke --deployment_id "<DEPLOYMENT_ID>" "<PROMPT>"
```

*If `deployment_id` is set in `config.toml`, omit the flag.*

```sh
watsonx-ai service invoke "<PROMPT>"
```

### ⚠️ Alternative flow: Python Script (Deprecated)

Follow these steps to inference your deployment. The [query_existing_deployment.py](examples/query_existing_deployment.py) file shows how to test the existing deployment using `watsonx.ai` library.

1. **Initialize the deployment ID**:

   Initialize the `deployment_id` variable in the [query_existing_deployment.py](examples/query_existing_deployment.py) file.  
   The _deployment_id_ of your deployment can be obtained from [the previous section](#%EF%B8%8F-deploying-on-ibm-cloud) by running [scripts/deploy.sh](scripts/deploy.py) 

2. **Run the script for querying the deployment**:

   ```sh
   python examples/query_existing_deployment.py
   ```

> [!WARNING]  
> This flow is deprecated and will be removed in a future release. Please migrate to recommended flow as soon as possible.

## 🖥️ Running the graphical app locally

You can also run the graphical application locally using the deployed model. All you need to do is deploy the model and follow the steps below. Detailed information for each app is available in its README file.

1. **Download the app**:

   ```bash
   watsonx-ai app new
   ```

2. **Configure the app**:

   All required variables are defined in the config.toml file.
   Here is an example of how to create the **WATSONX_BASE_DEPLOYMENT_URL**:
   `https://{REGION}.ml.cloud.ibm.com/ml/v4/deployments/{deployment_id}`


   ```bash
   cd <app_name>
   cp template.env .env
   ```

3. **Start the app**:

   ```bash
   watsonx-ai app run
   ```

3. **Start the app in development mode**:

   ```bash
   watsonx-ai app run --dev
   ```

   This soultion allows user to make changes to the source code while the app is running. Each time changes are saved the app reloads and is working with provided changes.

---

**Enjoy your coding! 🚀**

---

## 💾 Cloning template (Optional)

1. **Clone the repo** (sparse checkout):

   In order not to clone the whole `IBM/watsonx-developer-hub` repository we'll use git's shallow and sparse cloning feature to checkout only the template's directory:  
   
   ```sh
   git clone --no-tags --depth 1 --single-branch --filter=tree:0 --sparse https://github.com/IBM/watsonx-developer-hub.git
   cd watsonx-developer-hub
   git sparse-checkout add agents/base/crewai-websearch-agent
   cd agents/base/crewai-websearch-agent/
   ```

> [!NOTE]
> From now on it'll be considered that the working directory is `watsonx-developer-hub/agents/base/crewai-websearch-agent`  
