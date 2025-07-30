# A Base LangGraph LLM app template with function calling and persistent messages memory via database 🚀

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
* [Deleting a conversation by thread ID](#-deleting-a-conversation-by-thread-ID)
* [Running the graphical app locally](#%EF%B8%8F-running-the-graphical-app-locally) 
* [Cloning template (Optional)](#-cloning-template-optional)    


## 🤔 Introduction  

This repository provides the template for LLM apps built using LangGraph framework and database-backed memory for message storage. Specifically, the template demonstrates usage of Postgres database as a storage for short-term memory. By default, when using a conversation `thread_id`, the agent includes the context of the last 50 messages. This behavior can be modified by adjusting the `max_messages_in_context` variable in the [agent.py](src/langgraph_react_with_database_memory/agent.py) file. For more information about LangGrpah Persistence concept, please see [LangGraph documentation](https://langchain-ai.github.io/langgraph/concepts/persistence/). It also makes it easy to deploy them as an AI service as part of IBM watsonx.ai for IBM Cloud[^1].  
An AI service is a deployable unit of code that captures the logic of your generative AI use case. For and in-depth description of the topic please refer to the [IBM watsonx.ai documentation](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ai-services-templates.html?context=wx&audience=wdp). 

[^1]: _IBM watsonx.ai for IBM Cloud_ is a full and proper name of the component we're using in this template and only a part of the whole suite of products offered in the SaaS model within IBM Cloud environment. Throughout this README, for the sake of simplicity, we'll be calling it just an **IBM Cloud**.  

**Highlights:**

* 🚀 Easy-to-extend agent and tool modules
* ⚙️ Configurable via `config.toml`
* 🌐 Step-by-step local and cloud deployment 


## 🤖 The structure of ReAct agent

![alt text](react_agent_with_database_memory.png "LangGraph ReAct Agent")

## 🗂 Directory structure and file descriptions

The high level structure of the repository is as follows:  

```
langgraph-react-with-database-memory  
 ┣ src  
 ┃ ┗ langgraph_react_with_database_memory  
 ┃   ┣ agent.py  
 ┃   ┗ tools.py  
 ┣ schema  
 ┣ ai_service.py  
 ┣ config.toml.example  
 ┣ pyproject.toml  
```

* **`langgraph_react_with_database_memory`** folder: Contains auxiliary files used by the deployed function. They provide various framework specific definitions and extensions. This folder is packaged and sent to IBM Cloud during deployment as a [package extension](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ml-create-custom-software-spec.html?context=wx&audience=wdp#custom-wml).  
* **`schema`** folder: Contains request and response schemas for the `/ai_service` endpoint queries. Compared to the other templates, a new field `thread_id` has been added to `request.json`. When sending a request to the model, this field should be populated with the ID of the conversation thread. If the `thread_id` is not provided, only the content of the `messages` field will be passed to the model.  
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
   watsonx-ai template new "community/langgraph-react-with-database-memory"
   ```

   Upon executing the above command, a prompt will appear requesting the user to specify the target directory for downloading the template. Once the template has been successfully downloaded, navigate to the designated template folder to proceed.

> [!NOTE]
> Alternatively, it is possible to set up the template using a different method. For detailed instructions, please refer to the section "[Cloning template (Optional)](#-cloning-template-optional)".

3. **Install Poetry**:

   ```sh
   pipx install --python 3.11 poetry
   ```

4. **Install the template**:

    Running the below commands will install the repository in a separate virtual environment
   
   ```sh
   poetry install
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


The [agent.py](src/langgraph/agent.py) file builds app the graph consisting of nodes and edges. The former define the logic for agents while the latter control the logic flow in the whole graph.  
For detailed info on how to modify the graph object please refer to [LangGraph's official docs](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/#create-graph)  


The [ai_service.py](ai_service.py) file encompasses the core logic of the app alongside the way of authenticating the user to the IBM Cloud.  
For a detailed breakdown of the ai-service's implementation please refer the [IBM Cloud docs](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ai-services-create.html?context=wx)  


[tools.py](src/langgraph_react_agent_base/tools.py) file stores the definition for tools enhancing the chat model's capabilities.  
In order to add new tool create a new function, wrap it with the `@tool` decorator and add to the `TOOLS` list in the `extensions` module's [__init__.py](src/langgraph_react_agent_base/__init__.py)

For more sophisticated use cases (like async tools), please refer to the [langchain docs](https://python.langchain.com/docs/how_to/custom_tools/#creating-tools-from-runnables).  

## 🧪 Testing the template 

The `tests/` directory's structure resembles the repository. Adding new tests should follow this convention.  
For exemplary purposes only the tools and some general utility functions are covered with unit tests.  

Running the below command will run the complete tests suite:
```sh
poetry run pytest -r 'fEsxX' tests/
```  

## 💻 Running the application locally

It is possible to run (or even debug) the ai-service locally, however it still requires creating the connection to the IBM Cloud.

Ensure `config.toml` is configured.

You can test and debug your AI service locally via two alternative flows:


### ✅ Recommended flow: CLI

If you want to use your own payload, prepare it in a separate JSON file and specify the path to this file in the `payload_path` field in `config.toml`.

Example payload:
```json
{
        "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that uses tools to answer questions in detail."
                },
                {
                    "role": "user",
                    "content": "Hello!"
                }
        ],
        "thread_id": "814b39f8-4bb0-4d5b-ac1f-375e1fb0c1a6"
}
```
then run command:
```sh
watsonx-ai template invoke
```  

If you do not have a payload, run command below. But this case you cannot specify `thread_id`, so model will receive only your prompt.

```sh
watsonx-ai template invoke "<PROMPT>"
```


### 🔧 Alternative flow: Python Script

1. **Run Python Script**:

   ```sh
   poetry run python examples/execute_ai_service_locally.py
   ```

2. **Ask the model**:

   Choose from some pre-defined questions or ask the model your own.


## ☁️ Deploying on IBM Cloud 

Follow these steps to deploy the model on IBM Cloud.  

Ensure `config.toml` is configured, then run:

```sh
watsonx-ai service new
```

*Config file updates automatically with `deployment_id`.*

## 🔍 Querying the deployment

You can send inference requests to your deployed AI service via two alternative flows:

### ✅ Recommended flow: CLI

#### **If you have prepared payload**:    

```sh
watsonx-ai service invoke --deployment_id "<DEPLOYMENT_ID>"
```

*If `deployment_id` is set in `config.toml`, omit the flag.*

```sh
watsonx-ai service invoke
```  

#### **If you do now have prepared payload**: 
In this case you cannot specify `thread_id`, so model will receive only your prompt.

```sh
watsonx-ai service invoke --deployment_id "<DEPLOYMENT_ID>" "<PROMPT>"
```

*again if `deployment_id` is set in `config.toml`, omit the flag.*

```sh
watsonx-ai service invoke "<PROMPT>"
```

### 🔧 Alternative flow: Python Script
Follow these steps to inference your deployment. The [query_existing_deployment.py](examples/query_existing_deployment.py) file shows how to test the existing deployment using `watsonx.ai` library.

1. **Initialize the deployment ID**:

    Initialize the `deployment_id` and `thread_id` variables in the [query_existing_deployment.py](examples/query_existing_deployment.py) file.  
    The _deployment_id_ of your deployment can be obtained from `config.toml` file. 

2. **Run the script for querying the deployment**:

   ```sh
   poetry run python examples/query_existing_deployment.py
   ```
   When you run this command, a new conversation session is created and associated with your _thread_id_. This ID identifies the session and all its stored messages. If want, you can delete this conversation at any time - more informations you can find in [deleting a conversation by thread ID](#-deleting-a-conversation-by-thread-ID) section.


## 🗑 Deleting a conversation by thread ID
You can permanently remove the conversation associated with a specific thread.

1. **Initialize the thread ID**:

    Initialize the `thread_id` variable in the [clear_thread_history.py](examples/clear_thread_history.py) file.  
    
2. **Run the script for deleting the conversation**:

   ```sh
   poetry run python examples/clear_thread_history.py
   ```

> [!WARNING]  
> This action is **irreversible** and will permanently delete all data related to the thread.

## 🖥️ Running the graphical app locally

You can also run the graphical application locally using the deployed model. All you need to do is deploy the model and follow the steps below. In this case, the app will not use `thread_id`, so nothing will be saved in the database. Detailed information for each app is available in its README file.

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
   git sparse-checkout add agents/community/langgraph-react-with-database-memory
   cd agents/community/langgraph-react-with-database-memory/
   ```

> [!NOTE]
> From now on it'll be considered that the working directory is `watsonx-developer-hub/agents/community/langgraph-react-with-database-memory/`  