# AI Agent CI/CD Workflow

---

## Description

### Job Definitions

`test`: This job runs tests for the agent using `pytest`. It sets up the Python environment, caches Poetry dependencies, installs Poetry, and configures the environment for testing.
`validate`: This job follows the `test` job and sets up the environment for deployment. It configures the deployment settings, deploys the agent, invokes it, performs quality checks, and cleans up the deployment.
`deploy`: This job follows the `validate` job and deploys the agent to the production environment. It sets up the production-specific configuration and deploys the agent.

### Steps in Each Job

- **Checkout:** The latest code changes are checked out using `actions/checkout@v4`.
- **Python Setup:** The Python environment is set up using `actions/setup-python@v5` with the specified `PYTHON_VERSION`.
- **Caching:** Poetry dependencies and the virtual environment are cached using `actions/cache@v4` to speed up subsequent runs.
- **Poetry Installation:** Poetry is installed using a curl command to download the installer and add it to the system PATH.
- **Dependency Installation:** Project dependencies are installed using `poetry install` with `--with` flags for development or evaluation purposes.
- **Configuration:** Environment variables are set for WatsonX API keys, URL, and space ID, and a configuration script is run to set up the necessary files.
- **Agent Invocation:** The agent is invoked locally or in the deployment space using `watsonx-ai template invoke` or `watsonx-ai service invoke`.
- **Quality Checks:** A quality check script is run to validate the agent's code and setup.
- **Cleanup:** The deployment is removed using `watsonx-ai service delete` to clean up resources after testing or validation.

### Dependencies and Secrets

- The workflow uses GitHub Actions for version control, environment setup, and caching.
- Secrets for **watsonx** API keys, URL, and space IDs are managed securely by GitHub and accessed within the workflow using secrets.

### Workflow Triggers

- The workflow is triggered on pushes to the `main` branch.
- Jobs are structured to run sequentially, with `validate` depending on `test` and `deploy` depending on validate.

---

## User Guide

### Prerequisites

#### 1. GitHub Repository

- Ensure you have a GitHub repository containing the project files, including `deploy-agent.yaml` and necessary Python scripts.
- The repository should have the necessary permissions for the GitHub Actions runner to access and modify files.

#### 2. GitHub Repository Settings

- Navigate to your repository's **Settings** > **Secrets and variables** > **Actions**.
- In the **Secrets** tab create the following secrets:
  - **WATSONX_API_KEY**: Your watsonx API key, which provides access to the watsonx platform.
  - **WATSONX_URL**: The URL of your watsonx instance (e.g. `https://us-south.ml.cloud.ibm.com`).
  - **WATSONX_SPACE_ID_DEV**: The ID of your development space in watsonx.
  - **WATSONX_SPACE_ID_PROD**: The ID of your production space in watsonx.
- In the **Variables** tab create the following variables:
  - **AGENT_WORKDIR**: Working directory of your project relative to the root catalog of your repository (e.g. `agent/my-awesome-agent`).
  - **PYTHON_VERSION**: Versoin of a Python interpreter that you want to use in your workflow.

#### 3. GitHub Repository Files

- Copy the following files to the `.github/workflows` directory in your GitHub repository:
  - `deploy-agent.yaml`: file that contains workflow definition including worker and triggers specification.
- Add the following Python scripts to the directory specific to your agent location provided in `AGENT_WORKDIR` variable:
  - `setup-config.py`: This script sets up configuration files for both testing and deployment, using environment variables for Watsonx API keys, URL, and space IDs.
  - `quality-check.py`: This script performs quality checks on the agent's code and setup, ensuring it meets certain standards before deployment.

#### 4. Branch Protection (Optional but Recommended)

- To prevent accidental deployments, consider setting up branch protection for the `main` branch, requiring pull request reviews and status checks before merging.

### Required Access

- Repository Access: The GitHub Actions runner must have read access to your repository to fetch code and write access to create and delete resources during deployment.
- watsonx Access: The account associated with the `WATSONX_API_KEY` must have the necessary permissions to create and manage services in the specified spaces (`WATSONX_SPACE_ID_DEV` and `WATSONX_SPACE_ID_PROD`).

### Workflow Execution

- Once the prerequisites are met and secrets are configured, the workflow can be triggered automatically on pushes to the `main` branch.
- The workflow will execute the defined jobs (`test`, `validate`, and `deploy`), setting up the environment, running tests, configuring, deploying, and invoking the agent in both development and production spaces.

---
