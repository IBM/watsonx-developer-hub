#!/usr/bin/env bash

virtual_environment_name=$1
python_version=$2

if [ -x "$(command -v deactivate)" ]; then
    deactivate
fi

uv venv --clear --python=$python_version $virtual_environment_name
source "$virtual_environment_name/bin/activate"

uv run python -m ensurepip --upgrade
uv run python -m pip install --upgrade pip
uv pip install poetry pytest pytest-asyncio ibm-watsonx-ai-cli | tail -1
