# Templates

A catalog of templates designed to help you get started quickly with examples that can be easily customised, extended and deployed on the watsonx platform.

> **Note**
> Templates are moving to `base_sw_spec = "genai-A25-py3.12"`
> (previously `runtime-24.1-py3.11`).
> To use the old runtime, switch to the `rt-24_1` branch:
> https://github.com/IBM/watsonx-developer-hub/tree/rt-24_1

## Key features

- 🌐 **Framework agnostic**: Build solutions with any framework.
- ☁️ **Deployment**: Deploy as AI services with one command.

## Get started

### Quick Start Guide

Follow these steps to get started with any template:

#### 1. One-Time Setup

Before you begin, ensure you have the following installed on your system:

**Install the CLI and Poetry:**

Install or upgrade the IBM watsonx AI CLI tool:

```bash
pip install -U ibm-watsonx-ai-cli
```

Install Poetry package manager (if not already installed):

```bash
pipx install --python 3.11 poetry
```

**Prerequisites:**

- **Python 3.11-3.13** installed on your system
- **IBM Cloud account** with access to watsonx.ai (for IBM Cloud deployments) OR **watsonx.ai Software** installation (for on-premise deployments)
- **Deployment space** created in watsonx.ai

#### 2. Download a Template

List available templates:

```bash
watsonx-ai template list
```

Create a new template (interactive mode):

```bash
watsonx-ai template new
```

Or specify a template directly:

```bash
watsonx-ai template new "base/langgraph-react-agent"
```

The CLI will prompt you to specify a target directory for the template.

#### 3. Install Template Dependencies

Navigate to your template directory and install dependencies:

```bash
cd <your-template-directory>
poetry install --with dev
```

Optionally, activate the virtual environment:

```bash
source $(poetry -q env use 3.11 && poetry env info --path)/bin/activate
```

#### 4. Configure Environment Variables

Copy the template environment file and configure your credentials:

```bash
cp template.env .env
```

Edit the `.env` file with your credentials. **For security reasons, never hard-code credentials in your scripts or config files.**

**For IBM watsonx.ai for IBM Cloud deployments:**

```bash
# One of the below is required
WATSONX_APIKEY=<your-api-key>
WATSONX_TOKEN=

# Should follow the format: https://{REGION}.ml.cloud.ibm.com
WATSONX_URL=https://<region>.ml.cloud.ibm.com

# Deployment space ID (required)
WATSONX_SPACE_ID=<your-space-id>
```

You can find your IBM Cloud credentials at [Developer Access](https://dataplatform.cloud.ibm.com/developer-access).

**For on-premise (IBM watsonx.ai software) deployments:**

```bash
# Authentication: Choose ONE of the following methods:
# Method 1: API key + username
WATSONX_APIKEY=<your-api-key>
WATSONX_USERNAME=<your-username>

# Method 2: Password + username
WATSONX_PASSWORD=<your-password>
WATSONX_USERNAME=<your-username>

# Method 3: Token only
WATSONX_TOKEN=<your-token>

# Your watsonx.ai Software URL (required)
WATSONX_URL=<your-watsonx-software-url>

# Deployment space ID (required)
WATSONX_SPACE_ID=<your-space-id>
```

#### 5. Configure Deployment Settings

Copy the configuration template:

```bash
cp config.toml.example config.toml
```

Edit `config.toml` file to configure deployment parameters:

```toml
[cli.options]
  stream = true
  payload_path = ""

[deployment.online.parameters]
  model_id = "ibm/granite-4-h-small"
  url = "https://us-south.ml.cloud.ibm.com"  # should follow the format: `https://{REGION}.ml.cloud.ibm.com`

[deployment.software_specification]
  name = ""
  overwrite = false
  base_sw_spec = "genai-A25-py3.12"
```

#### 6. Test Locally

Before deploying, test your template locally:

```bash
watsonx-ai template invoke "Hello, how can you help me?"
```

#### 7. Deploy Your AI Service

Deploy your template as an AI service:

```bash
watsonx-ai service new
```

This command will:

1. Build a package extension from your template
2. Create or update a software specification
3. Deploy the AI service to your watsonx.ai space

#### 8. Query the Deployment

Once deployed, invoke your AI service:

```bash
watsonx-ai service invoke "Hello from the cloud!"
```

#### 9. Manage Deployments

List all deployments in your space:

```bash
watsonx-ai service list
```

Delete a deployment:

```bash
watsonx-ai service delete <deployment-id>
```

## Official Templates

| Template                                                       |
| -------------------------------------------------------------- |
| [LangGraph](./base/langgraph-react-agent/)                     |
| [LlamaIndex](./base/llamaindex-websearch-agent/)               |
| [CrewAI](./base/crewai-websearch-agent/)                       |
| [AutoGen](./base/autogen-agent/)                               |
| [BeeAI React Agent](./base/beeai-framework-requirement-agent/) |
| [BeeAI Workflow](./base/beeai-framework-workflow/)             |

## Community Templates

Templates published and maintained by the community.

| Template                                                                                 | Framework | Description                                                                                                                 | CLI support |
| ---------------------------------------------------------------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------------- | ----------- |
| [Agentic RAG](./community/langgraph-agentic-rag/)                                        | Langraph  | Agent to improve retrieval augmented generation (RAG) scenario.                                                             | Yes         |
| [arXiv Research Agent](./community/langgraph-arxiv-research/)                            | Langraph  | Agent to search and summarize research papers published on arXiv.                                                           | Yes         |
| [arXiv Research Model Gateway Agent](./community/langgraph-arxiv-research-model-gateway) | Langraph  | Agent to route requests to LLM providers using Model Gateway.                                                               | Yes         |
| [Graph RAG Agent](./community/langgraph-graph-rag)                                       | Langraph  | Agent to solve RAG tasks by combining Neo4j-powered knowledge graphs with vector similarity search.                         | Yes         |
| [Agent with Human In The Loop architecture](./community/langgraph-human-in-the-loop/)    | Langraph  | Agent that follows Human In The Loop architecture.                                                                          | partial     |
| [Agent with database memory](./community/langgraph-react-with-database-memory)           | Langraph  | Agent to manage conversation memory using a Postgres database, retaining context from recent messages for LLM interactions. | Yes         |
| [Agentic SQL RAG](./community/langgraph-sql-rag/)                                        | Langraph  | Agentic RAG template for querying SQL databases with LLMs                                                                   | Yes         |
| [Agent with the Tavily search Tool](./community/langgraph-tavily-tool/)                  | Langraph  | Agent that uses Tavily search tool and IBM Cloud® Secrets Manager.                                                          | Yes         |
| [Agent with MCP server and AutoAI model](./community/mcp-autoai-template/)               | Langraph  | Agent that uses MCP Server to interact with a deployed AutoAI model.                                                        | No          |

## Videos with Quickstart

### [Graph RAG Agent](./community/langgraph-graph-rag)

https://github.com/user-attachments/assets/a8666d3f-cedd-435b-a4de-89da8eae1ccb

### [Agent with Human In The Loop architecture](./community/langgraph-human-in-the-loop)

https://github.com/user-attachments/assets/89a26ab3-d592-4ede-9acf-2f7f99a8d799

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Module not found" errors during local testing

**Solution**: Ensure you've installed dependencies and activated the virtual environment:

```bash
poetry install --with dev
source $(poetry env info --path)/bin/activate
```

#### Issue: "Authentication failed" when deploying

**Solution**: Verify your credentials in the `.env` file:

- Check that `WATSONX_APIKEY`/`WATSONX_TOKEN` (or `WATSONX_USERNAME`/`WATSONX_PASSWORD` for on-premise) is valid and not expired
- Ensure `WATSONX_URL` matches your region (IBM Cloud) or your watsonx.ai Software installation (on-premise)
- Confirm `WATSONX_SPACE_ID` exists and you have access

#### Issue: Deployment fails with "Software specification not found"

**Solution**: The base software specification may have changed. Update `config.toml`:

```toml
[deployment.software_specification]
base_sw_spec = "genai-A25-py3.12"
```

#### Issue: Local invoke works but deployment fails

**Solution**: Check for dependencies that aren't compatible with the cloud environment:

- Ensure all dependencies are listed in `pyproject.toml`
- Avoid system-specific packages
- Test with the same Python version (3.11) used in deployment

#### Issue: Streaming responses not working

**Solution**:

1. Verify `stream = true` in `config.toml`
2. Ensure `generate_stream()` function is implemented in `ai_service.py`

#### Issue: "Space not found" error

**Solution**: Create a deployment space in watsonx.ai:

1. Go to [IBM Cloud watsonx.ai](https://dataplatform.cloud.ibm.com/) (or your watsonx.ai Software installation)
2. Navigate to Deployments > Spaces
3. Create a new deployment space
4. Copy the space ID to your `.env` file as `WATSONX_SPACE_ID`

### Getting Help

If you encounter issues not covered here:

1. Check the [watsonx.ai documentation](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ai-services-templates.html)
2. Review template-specific README files for additional guidance
3. Join our [Discord community](https://ibm.biz/wx-discord) for support
4. Open an issue on [GitHub](https://github.com/IBM/watsonx-developer-hub/issues)

## Template Requirements

Ensuring seamless integration and full lifecycle support, all templates must comply with the following requirements. These requirements ensure that the same instructions can be used consistently across all templates.

### 1. Discoverability Requirements

The CLI must automatically detect, list, and initialize the template without manual intervention. Discovered templates must be listed by the following commands:

- `watsonx-ai template list`
- `watsonx-ai template new`

> **Note:** Templates will only appear in the `listing` commands once they have been merged into the `main` branch.

**Repository Placement**
The template directory must exist on the `main` branch under one of the following folders:

- `agents/base/<template-name>/`
- `agents/community/<template-name>/`

**Template Categories**

- **Base templates:** Curated and maintained by IBM developers, these provide a foundational starting point for building more advanced applications.

- **Community templates:** Contributed by the wider community, these showcase more advanced solutions and include integrations with external tools—such as web search, retrieval-augmented generation (RAG), or custom toolkits—to solve specialized problems.

> **Naming:** Use kebab-case (e.g., `my-new-agent`).  
> **Uniqueness:** No duplicate `<template-name>` values across **base** and **community** folders.

### 2. End-to-End Usability Requirements

#### 2.1. Minimal Template Structure

The CLI validation logic will confirm the presence of:

- **ai_service.py** - File contains the function to be deployed as an AI service defining the application's logic.
- **pyproject.toml** - Defines package metadata and dependency declarations.
- **src/** - Folder contains the Python package with source code.
- **template.env** - Template for environment variables containing credentials (copied to `.env`).
- **config.toml.example** - Configuration file for deployment parameters (copied to `config.toml`).
- **schema/** - Folder contains request and response schemas for the `/ai_service` endpoint queries.
- **README.md** - Provides user guidance following the same structure as this document

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

  > _Tip:_ Add dev-only dependencies under `[tool.poetry.dev-dependencies]` if needed.

* A valid `LICENSE` file must be present for legal compliance

#### 2.3. Service Entry Point

In the `ai_service.py` file, define an external function with `context` as its first parameter. Within this function, implement at least one of the following handlers (implement both if required):

- **`def generate(context) -> dict:`**
  - Handles synchronous REST calls to `/ml/v4/deployments/{id}/ai_service`.
  - Returns a JSON object containing a `choices` array.

- **`def generate_stream(context) -> Generator[dict, None, None]:`**
  - Handles SSE calls to `/ml/v4/deployments/{id}/ai_service_stream`.
  - Yields incremental `choices` with `delta` updates.

#### 2.4. Application Logic & Tools

- The `src/<python_package>/` directory must be a valid Python package (include an `__init__.py` file) containing all application and tool implementations.

- Filenames are flexible but should clearly convey purpose and be importable (e.g., `workflow.py`, `graph_builder.py`, `custom_tools.py`).

- Implement core workflows, graph constructions, or orchestration in one or more modules.

- Define external tool integrations in separate modules, annotated appropriately (e.g., `@tool`).

#### 2.5. Configuration Management

Templates use a two-file configuration approach:

1. **`.env` file**: Contains all credentials and authentication parameters
   - Copy from `template.env` and fill in your credentials
   - Never commit this file to version control
   - Environment variables are automatically loaded by the CLI

2. **`config.toml` file**: Contains deployment parameters
   - Copy from `config.toml.example` if the template requires it
   - Configures model selection, runtime settings, and deployment options
   - Some templates may require specific configuration options

This separation ensures security (credentials in `.env`) while maintaining flexibility (deployment parameters in `config.toml`).

#### 2.6. Schema Definitions

- The `schema/` folder must include two JSON Schema files:
  - **`request.json`** — Describes the expected request payload, typically defining an array of `messages` where each message has a `role` (user, assistant, system) and `content`.
  - **`response.json`** — Captures both synchronous and streaming responses; it specifies an array of `choices`, each containing either a `message` (for sync) or a `delta` update (for streaming).

> Note: Schema definitions may evolve over time. Ensure each JSON schema remains valid and aligned with the watsonx.ai service API.

#### 2.7. Documentation

- **`README.md`** must cover:
  - Introduction & purpose
  - Directory structure overview
  - Prerequisites (Poetry/pipx, Python version)
  - Setup & install steps
  - Local invoke instructions (`watsonx-ai template invoke "<query>"`)
  - Remote deploy & invoke steps (`watsonx-ai service new`, `watsonx-ai service invoke`)
  - How to extend (adding tools, parameters)

- Follow the style of existing [base templates](https://github.com/IBM/watsonx-developer-hub/tree/main/agents/base).

## Contributing Guidelines

We’re really excited that you’re considering contributing to this project! Every contribution, no matter how small, makes a difference – and we’d be truly happy to have you on board.

### Getting Started

This repository is open to contributions from everyone. Whether you’d like to fix a bug, improve documentation, or add a brand-new template – your input is valuable.
To keep everything consistent, please make sure your templates follow our guidelines.
You can find the detailed requirements in the [previous section](#template-requirements) of this README.
If you are new to watsonx Developer Hub, we recommend reading the [Code of Conduct](../CODE_OF_CONDUCT.md).

### Working on Existing Issues

1. Check the Issues section for open tasks.
2. If you find an issue related to a specific template that interests you, reach out to us first.
3. We’ll assign the issue to you, so others know it’s in progress and there’s no overlap.

### Proposing New Ideas

Got a new idea that’s not in the issues list? Awesome!
We encourage you to share it with us – simply open a discussion or contact us directly. We’ll be glad to review it together and figure out how it fits into the project.

### Issues and pull requests

We use GitHub pull requests to accept contributions.

While not required, it’s a good idea to open a new issue for the bug you’re fixing or the feature you’re working on before submitting a pull request.
This helps start a discussion with the community about your work, provides a place to refine the idea and figure out the best way to implement it, and lets others know what you’re working on.
If you need help, you can also reference the issue when discussing it with community members or the team.

### Developer Certificate of Origin (DCO)

We have tried to make it as easy as possible to make contributions. This applies to how we handle the legal aspects of contribution. We use the [Developer's Certificate of Origin 1.1 (DCO)](https://developercertificate.org/) to manage code contributions.
When submitting a patch for review, the developer must include a sign-off statement in the commit message. If you set your user.name and user.email in your git config file, you can sign your commit automatically by using the following command:

```bash
git commit -s
```

If a commit has already been created but signoff was missed this can be remedied

```bash
git commit --amend -s
```

The following example includes a `Signed-off-by:` line, which indicates that the submitter has accepted the DCO:

```txt
Signed-off-by: John Doe <john.doe@example.com>
```

We automatically verify that all commit messages contain a `Signed-off-by:` line with your email address.

## Consuming deployed services

All of the available templates can be easily consumed in the [React UI App](../apps/base/nextjs-chat-with-ai-service/) that creates local running React application providing users an option to interact with deployed AI services. To run the app locally please follow these [steps](../apps/base/nextjs-chat-with-ai-service/README.md).

## Support

See the [watsonx Developer Hub](https://ibm.com/watsonx/developer) for quickstarts and documentation. Please reach out to us on [Discord](https://ibm.biz/wx-discord) if you have any questions or want to share feedback. We'd love to hear from you!
