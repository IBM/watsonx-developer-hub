import os
import shutil
import subprocess
import sys


def install_package(package_name: str):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])


def create_config(template_file: str, target_file: str):
    from tomlkit import parse, dumps

    # Copy template
    if os.path.exists(template_file):
        shutil.copyfile(template_file, target_file)
    else:
        raise FileNotFoundError(f"Configuration template file {template_file} does not exist!")

    # Parse and fill with values from env variables
    with open(target_file, "r") as f:
        config = parse(f.read())

    config["deployment"]["watsonx_apikey"] = os.getenv("WATSONX_API_KEY", "")
    config["deployment"]["watsonx_url"] = os.getenv("WATSONX_URL", "")
    config["deployment"]["space_id"] = os.getenv("WATSONX_SPACE_ID", "")
    config["deployment"]["deployment_id"] = os.getenv("DEPLOYMENT_ID", "")

    # TODO - consider changing sw_spec name with timestamp, as a temp solution set overwrite flag
    config["deployment"]["software_specification"]["overwrite"] = True

    with open(target_file, "w") as f:
        f.write(dumps(config))
