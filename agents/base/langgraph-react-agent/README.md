# A Base LangGraph LLM app template with function calling capabilities 🚀

## 📖 Table of Contents
* [Introduction](#-introduction)  
* [Directory structure and file descriptions](#-directory-structure-and-file-descriptions)  
* [Prerequisites](#-prerequisites)  
* [Installation](#-installation)
* [Configuration](#-configuration) 
* [Modifying and configuring the template](#-modifying-and-configuring-the-template)  
* [Testing the template](#-testing-the-template)  
* [Running the application locally](#-running-the-application-locally)  
* [Deploying on IBM Cloud](#-deploying-on-ibm-cloud) 
* [Querying the deployment](#-querying-the-deployment)  
* [Running the graphical app locally](#-running-the-graphical-app-locally) 
* [Evaluating agent](#-evaluating-agent)
* [Cloning template (Optional)](#-cloning-template-optional)  

## 🤔 Introduction

This repository provides a basic template for LLM apps built using the LangGraph framework. It also makes it easy to deploy them as an AI service as part of IBM watsonx.ai for IBM Cloud[^1].

An AI service is a deployable unit of code that encapsulates the logic of your generative AI use case. For an in-depth description of AI services, please refer to the [IBM watsonx.ai documentation](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ai-services-templates.html?context=wx&audience=wdp).

[^1]: _IBM watsonx.ai for IBM Cloud_ is a full and proper name of the component we're using in this template and only a part of the whole suite of products offered in the SaaS model within IBM Cloud environment. Throughout this README, for the sake of simplicity, we'll be calling it just an **IBM Cloud**.

**Highlights:**

* 🚀 Easy-to-extend agent and tool modules
* ⚙️ Configurable via `config.toml`
* 🌐 Step-by-step local and cloud deployment

## 🗂 Directory structure and file descriptions

The high level structure of the repository is as follows:  

```
langgraph-react-agent/
├── src/
│   └── langgraph_react_agent_base/
│       ├── agent.py
│       └── tools.py
├── schema/
├── ai_service.py
├── config.toml.example
├── template.env
└── pyproject.toml
```

* **`langgraph-react-agent-base`** folder: Contains auxiliary files used by the deployed function. They provide various framework specific definitions and extensions. This folder is packaged and sent to IBM Cloud during deployment as a [package extension](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ml-create-custom-software-spec.html?context=wx&audience=wdp#custom-wml).  
* **`schema`** folder: Contains request and response schemas for the `/ai_service` endpoint queries.  
* **`ai_service.py`** file: Contains the function to be deployed as an AI service defining the application's logic  
* **`config.toml.example`**: A configuration file with placeholders that stores the deployment metadata. After downloading the template repository, copy the contents of the `config.toml.example` file to the `config.toml` file and fill in the required fields. `config.toml` file can also be used to tweak the model for your use case. 
* **`template.env`**: A file with placeholders for necessary credentials that are essential to run some of the `ibm-watsonx-ai-cli` commands and to test agent locally. Copy the contents of the `template.env` file to the `.env` file and fill the required fields.

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
   watsonx-ai template new "base/langgraph-react-agent"
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

1. Copy `template.env` → `.env`.
2. Copy `config.toml.example` → `config.toml`.
3. Fill in IBM Cloud credentials.

## 🎨 Modifying and configuring the template

[config.toml](config.toml) and [.env](.env) files should be filled in before either deploying the template on IBM Cloud or executing it locally.  
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
pytest -r 'fEsxX' tests/
```

## 💻 Running the application locally

It is possible to run (or even debug) the ai-service locally, however it still requires creating the connection to the IBM Cloud.

Ensure `config.toml` and `.env` are configured.

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

Ensure `config.toml` and `.env` are configured.

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

*If `deployment_id` is set in `.env`, omit the flag.*

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

   All required variables are defined in the `.env` file.
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

   This solution allows user to make changes to the source code while the app is running. Each time changes are saved the app reloads and is working with provided changes.

## 📊 Evaluating agent
`IBM watsonx.ai CLI` allows you to evaluate agent responses using your own datasets prepared in JSONL format. It supports using multiple metrics for comprehensive evaluation. The metrics are calculated using the **IBM watsonx.governance SDK** library. You can find more details about these metrics in the official documentation [here](https://ibm.github.io/ibm-watsonx-gov/). If you want to evaluate your agent, you can do so using the following command.

**Example usage:**
```bash
$ watsonx-ai template eval --tests test1.jsonl,test2.jsonl --metrics answer_similarity,answer_relevance --evaluator llm_as_judge
```

The `eval` command supports several options

### Available options and arguments
- `--help`: Show this message and exit.
- `--tests`: **[Required]** one or more input data files (in JSONL format) for evaluation. If more than one evaluation file is provided, they must be separated by a comma.  
 The required fields in the files are described in the section below.
- `--metrics`: **[Optional]** one or more evaluation metrics. If multiple metrics are specified, they must be separated by a comma. If not specified all possible metrics will be used (answer_similarity, answer_relevance, text_reading_ease, unsuccessful_request_metric,text_grade_level)
- `--evaluator`: **[Optional]** a model name for evaluation, or `llm_as_judge` can be used for a predefined choice (`meta-llama/llama-3-3-70b-instruct`, or `mistralai/mistral-small-3-1-24b-instruct-2503 if former is not available` if former is not available). 
  - If not provided, metrics are computed using the `token_recall` method.  
  - If provided, two metrics **answer similarity** and **answer relevance** are calculated using llm as judge method.  
    The remaining metrics are still calculated using the rule-based method.

### Requirements

* **IBM Cloud**: Add your API key to the environment variables.
* **CPD**: Add either a username and password, or a username and API key, to the environment variables.


All variables can be defined in a .env file.
When selecting a specific model as the evaluation judge, ensure that the model is available in your space. By default, the evaluation uses:

* `meta-llama/llama-3-3-70b-instruct`
* `mistralai/mistral-small-3-1-24b-instruct-2503` (fallback if the first model is unavailable)

If no evaluation model is specified, at least one of the above must be available in your space.

### Evaluation data format
For each file, metrics are calculated separately.  
The data must be in JSONL format. Each row should contain two fields:  
- `input`: a string representing the input.  
- `ground_truth`: a list of strings representing the correct answers.  

During evaluation, answers are generated based on the `input` and compared to the `ground_truth` only for metrics that require it.

### Available types of metrics
The evaluation supports the following metric types:

- **answer_similarity**  
  Measures how similar the agent’s response is to the `ground_truth`.  
  By default, it uses the `token_recall` method. If the `--evaluator` flag is set, it switches to an LLM-based evaluation.

- **answer_relevance**  
  Measures how relevant the response is to the input query.  
  By default, it also uses `token_recall`, but with `--evaluator`, it uses the LLM to judge relevance.

- **text_reading_ease**  
  Assesses the readability of the generated text using the Flesch Reading Ease formula.  
  This metric always uses a fixed rule-based method and ignores the `--evaluator` flag.

- **unsuccessful_request_metric**  
  Checks whether the response indicates a failed or incomplete answer by scanning for predefined failure phrases.  
  This is a rule-based check and does not change even if `--evaluator` is provided.

- **text_grade_level**  
  Estimates the U.S. school grade level required to understand the response using the Flesch–Kincaid Grade formula.  
  This metric is rule-based and ignores the `--evaluator` setting.

### Evaluation result
Metrics are calculated for each test file separately, so also the output is displayed for each file. For each file and metric it is displayed in JSON style. 
In the begging are summary information about results for metric and whole file. Next there are informations for each row in file separately. 

### Evaluation Results

* Metrics are calculated per test file.
* Results are displayed in JSON format for each file and metric.
* The output begins with summary information for the file and metrics, followed by row-level details.

**Example: Single result for one metric**

```JSON
{
  "name": "answer_similarity",
  "method": "llm_as_judge",
  "provider": "unitxt",
  "value": 0.0,
  "errors": null,
  "additional_info": null,
  "group": "answer_quality",
  "thresholds": [
    {
      "type": "lower_limit",
      "value": 0.7
    }
  ],
  "min": 0.0,
  "max": 0.0,
  "mean": 0.0,
  "total_records": 3,
  "record_level_metrics": [
    {
      "name": "answer_similarity",
      "method": "llm_as_judge",
      "provider": "unitxt",
      "value": 0.0,
      "errors": null,
      "additional_info": null,
      "group": "answer_quality",
      "thresholds": [
        {
          "type": "lower_limit",
          "value": 0.7
        }
      ],
      "record_id": "44e17041-51ac-4f65-8e2f-e9afd082b940",
      "record_timestamp": null
    },
    {
      "name": "answer_similarity",
      "method": "llm_as_judge",
      "provider": "unitxt",
      "value": 0.0,
      "errors": null,
      "additional_info": null,
      "group": "answer_quality",
      "thresholds": [
        {
          "type": "lower_limit",
          "value": 0.7
        }
      ],
      "record_id": "67b58b7e-2990-4559-97a9-680e01068e3f",
      "record_timestamp": null
    }
  ]
}
```

> [!WARNING]  
> The `eval` command requires Python version >=3.10,<=3.12

---

**Enjoy your coding! 🚀**

---




## 💾 Cloning template (Optional)

1. **Clone the repo** (sparse checkout):

   In order not to clone the whole `IBM/watsonx-developer-hub` repository we'll use git's shallow and sparse cloning feature to checkout only the template's directory:  
   
   ```sh
   git clone --no-tags --depth 1 --single-branch --filter=tree:0 --sparse https://github.com/IBM/watsonx-developer-hub.git
   cd watsonx-developer-hub
   git sparse-checkout add agents/base/langgraph-react-agent
   cd agents/base/langgraph-react-agent/
   ```

> [!NOTE]
> From now on it'll be considered that the working directory is `watsonx-developer-hub/agents/base/langgraph-react-agent/`  
