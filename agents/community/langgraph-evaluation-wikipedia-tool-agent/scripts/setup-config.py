import os
import shutil
from tomlkit import parse, dumps


# Setup config.toml
config_file = "config.toml"
config_template = f"{config_file}.example"

def create_config(template_file: str, target_file: str):
    """
    This function creates a config.toml file by copying a template and populating it with environment variables.

    Args:
        template_file (str): The path to the configuration template file.
        target_file (str): The path where the new config.toml file will be created.

    Raises:
        FileNotFoundError: If the template file does not exist.
        KeyError: If the 'deployment' section is missing in the target file.
    """

    # Copy template
    if os.path.exists(template_file):
        shutil.copyfile(template_file, target_file)
    else:
        raise FileNotFoundError(f"Configuration template file {template_file} does not exist!")

    # Parse and fill with values from env variables
    with open(target_file, "r") as f:
        config = parse(f.read())

    deployment_section_name = "deployment"

    if deployment_section_name not in config.keys():
        raise KeyError(f"Configuration section {deployment_section_name} not found in {target_file}")

    # Fill in config values from environment variables
    config[deployment_section_name]["watsonx_apikey"] = os.getenv("WATSONX_API_KEY", "")
    config[deployment_section_name]["watsonx_url"] = os.getenv("WATSONX_URL", "")
    config[deployment_section_name]["space_id"] = os.getenv("WATSONX_SPACE_ID", "")
    config[deployment_section_name]["deployment_id"] = os.getenv("DEPLOYMENT_ID", "")

    # Map the same url for online parameters
    config[deployment_section_name]["online"]["parameters"]["url"] = config[deployment_section_name]["watsonx_url"]

    # Temporarily set 'overwrite' flag to True in 'software_specification'
    config[deployment_section_name]["software_specification"]["overwrite"] = True

    # Write the updated config to the target file
    with open(target_file, "w") as f:
        f.write(dumps(config))

# Call the function to create the config file
create_config(config_template, config_file)
