import os
import shutil
from utils import install_package


# Install CLI
install_package("ibm-watsonx-ai-cli")

# Install poetry required for deployment
install_package("poetry")

# Setup config.toml
agent_workdir = os.environ["AGENT_WORKDIR"]
config_file = f"{agent_workdir}/config.toml"
config_template = f"{config_file}.example"

# Copy template
if os.path.exists(config_template):
    shutil.copyfile(config_template, config_file)
else:
    raise FileNotFoundError(f"Configuration file {config_file} does not exist!")

# Inject variables
try:
    import toml
except ImportError:
    install_package("toml")
    import toml

with open(config_file, "r") as f:
    config = toml.load(f)

config["deployment"]["watsonx_apikey"] = os.environ["WATSONX_API_KEY"]
config["deployment"]["watsonx_url"] = os.environ["WATSONX_URL"]
config["deployment"]["space_id"] = os.environ["WATSONX_SPACE_ID"]

# TODO - consider changing sw_spec name with timestamp, as a temp solution set overwrite flag
config["deployment"]["software_specification"]["overwrite"] = True

with open(config_file, "w") as f:
    toml.dump(config, f)
