# Agents

A catalog of templates designed to help you get started quickly with examples that can be easily customised, extended and deployed on the watsonx platform.

## Key features

- 🌐 **Framework agnostic**: Build agents with any framework.
- ☁️ **Deployment**: Deploy agents as AI services with one command.

## Get started

1. **Install** the CLI 

```bash
pip install ibm-watsonx-ai-cli
```

2. **Create** the template

```bash
watsonx-ai template new
```

3. **Configure** the template

Go to the [Developer Access](https://dataplatform.cloud.ibm.com/developer-access) to find your environment variables.

```bash
cp config.toml.example config.toml
```

4. **Run** the template

```bash
watsonx-ai template invoke "Hello"
```

5. **Deploy** the template

```bash
watsonx-ai service new
```

6. **Run** the deployment

```bash
watsonx-ai service invoke "Hello"
```

## Official Templates

Designed to help you get started quickly with examples that can be easily customized and extended.

| Template                 | 
| ------------------------ |
| [LangGraph](./base/langgraph-react-agent/) |
| [LlamaIndex](./base/llamaindex-websearch-agent/) |
| [CrewAI](./base/crewai-websearch-agent/) |
| [AutoGen](./base/autogen-agent/) |
| [BeeAI React Agnet](./base/beeai-framework-react-agent/) |
| [BeeAI Workflow](./base/beeai-framework-workflow/) |

## Community Templates

Templates published and maintained by the community.

| Template                                            | Framework | Description                                                       | CLI support |
| --------------------------------------------------- | --------- | ----------------------------------------------------------------- | ----------- |
| [Agentic RAG](./community/langgraph-agentic-rag/) | Langraph  | Agent to improve retrieval augmented generation (RAG) scenario. | Yes |
| [arXiv Research Agent](./community/langgraph-arxiv-research/) | Langraph  | Agent to search and summarize research papers published on arXiv. | Yes |
| [Agent with the Tavily search Tool](./community/langgraph-tavily-tool/) | Langraph  | Agent that uses Tavily search tool and IBM Cloud® Secrets Manager. | Yes | 
| [Agent with MCP server and AutoAI model](./community/mcp-autoai-template/) | Langraph  | Agent that uses MCP Server to interact with a deployed AutoAI model. | No |

## Template Requirements

Ensuring seamless integration and full lifecycle support, all agent templates must comply with the following requirements.

### 1. Discoverability Requirements

The CLI must automatically detect, list, and initialize the template without manual intervention. Discovered templates must be listed by the following commands:

* `watsonx-ai template list`
* `watsonx-ai template new`

> **Note:** Templates will only appear in the `listing` commands once they have been merged into the `main` branch.

**Repository Placement**
The template directory must exist on the `main` branch under one of the following folders:

* `agents/base/<template-name>/`
* `agents/community/<template-name>/`

**Template Categories**

* **Base templates:** Curated and maintained by IBM developers, these provide a foundational starting point for building more advanced applications.

* **Community templates:** Contributed by the wider community, these showcase more advanced agents and include integrations with external tools—such as web search, retrieval-augmented generation (RAG), or custom toolkits—to solve specialized problems.

> **Naming:** Use kebab-case (e.g., `my-new-agent`).  
> **Uniqueness:** No duplicate `<template-name>` values across **base** and **community** folders.

### 2. End-to-End Usability Requirements

#### 2.1. Minimal Template Structure

The CLI validation logic will confirm the presence of:

* **ai_service.py** - File contains the function to be deployed as an AI service defining the application's logic.
* **pyproject.toml** - Defines package metadata and dependency declarations.
* **src/** - Folder contains the Python package with Agent source code.
* **config.toml.example** - A configuration file with placeholders that stores the deployment metadata.
* **schema/** - Folder contains request and response schemas for the `/ai_service` endpoint queries.
* **README.md** - Provides user guidance

#### 2.2. Dependency & Metadata Compliance

- **Mandatory fields** in `pyproject.toml`:

    ```toml
    [tool.poetry]
    name = "<package_name>"
    version = "<package_version>"

    [tool.poetry.dependencies]
    python = ">=3.10,<3.13"

    [build-system]
    requires = ["poetry-core"]
    build-backend = "poetry.core.masonry.api"
    ```

- **Optional metadata** (improves discoverability):

    - `description`
    - `authors`
    - `license`
    - `readme`
    - `packages`

    > *Tip:* Add dev-only dependencies under `[tool.poetry.dev-dependencies]` if needed.

* A valid `LICENSE` file must be present for legal compliance

#### 2.3. Service Entry Point

In the `ai_service.py` file, define an external function with `context` as its first parameter. Within this function, implement at least one of the following handlers (implement both if required):

* **`def generate(context) -> dict:`**
    - Handles synchronous REST calls to `/ml/v4/deployments/{id}/ai_service`.
    - Returns a JSON object containing a `choices` array.

* **`def generate_stream(context) -> Generator[dict, None, None]:`**
    - Handles SSE calls to `/ml/v4/deployments/{id}/ai_service_stream`.
    - Yields incremental `choices` with `delta` updates.

#### 2.4. Agent Logic & Tools

* The `src/<python_package>/` directory must be a valid Python package (include an `__init__.py` file) containing all agent and tool implementations.

* Filenames are flexible but should clearly convey purpose and be importable (e.g., `workflow.py`, `graph_builder.py`, `custom_tools.py`). 

* Implement core workflows, graph constructions, or orchestration in one or more modules.

* Define external tool integrations in separate modules, annotated appropriately (e.g., `@tool`).

#### 2.5. Configuration Management

After downloading the template repository, copy the contents of the `config.toml.example` file to the `config.toml` file and fill in the required fields. `config.toml` file can also be used to tweak the model for your use case. 

#### 2.6. Schema Definitions

* The `schema/` folder must include two JSON Schema files:
    - **`request.json`** — Describes the expected request payload, typically defining an array of `messages` where each message has a `role` (user, assistant, system) and `content`.
    - **`response.json`** — Captures both synchronous and streaming responses; it specifies an array of `choices`, each containing either a `message` (for sync) or a `delta` update (for streaming).

> Note: Schema definitions may evolve over time. Ensure each JSON schema remains valid and aligned with the watsonx.ai service API.

#### 2.7. Documentation

* **`README.md`** must cover:

    - Introduction & purpose
    - Directory structure overview
    - Prerequisites (Poetry/pipx, Python version)
    - Setup & install steps
    - Local invoke instructions (`watsonx-ai template invoke "<query>"`)
    - Remote deploy & invoke steps (`watsonx-ai service new`, `watsonx-ai service invoke`)
    - How to extend (adding tools, parameters)

* Follow the style of existing [base templates](https://github.com/IBM/watsonx-developer-hub/tree/main/agents/base).

## Consuming deployed agents

All of the available templates can be easily consumed in the [React UI App](../apps/base/nextjs-chat-with-ai-service/) that creates local running React application providing users an option to infer agents. To run the app local please follow these [steps](../apps/base/nextjs-chat-with-ai-service/README.md).

## Support

See the [watsonx Developer Hub](https://ibm.com/watsonx/developer) for quickstarts and documentation. Please reach out to us on [Discord](https://ibm.biz/wx-discord) if you have any questions or want to share feedback. We'd love to hear from you!
