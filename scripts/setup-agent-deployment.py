import os
from utils import create_config, install_package


# Install CLI
install_package("ibm-watsonx-ai-cli")

# Install poetry required for deployment
install_package("poetry")

# Setup config.toml
agent_workdir = os.getenv("AGENT_WORKDIR", ".")
config_file = f"{agent_workdir}/config.toml"
config_template = f"{config_file}.example"

create_config(config_template, config_file)
