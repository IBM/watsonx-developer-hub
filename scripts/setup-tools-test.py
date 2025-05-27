import os
import subprocess
from utils import install_package

# Install poetry required for deployment
install_package("poetry")

# Install the template with poetry
agent_workdir = agent_workdir = os.getenv("AGENT_WORKDIR", ".")
subprocess.check_call(
    ["poetry", "install", "--with", "dev", "--directory", agent_workdir]
)
