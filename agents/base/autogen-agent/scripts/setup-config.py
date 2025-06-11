import os
import shutil


# Setup config.toml
config_file = f"config.toml"
config_template = f"{config_file}.example"

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

    deployment_section_name = "deployment"
    
    if deployment_section_name not in config.keys():
        raise KeyError(f"Configuration section {deployment_section_name} not found in {target_file}")
    
    config[deployment_section_name]["watsonx_apikey"] = os.getenv("WATSONX_API_KEY", "")
    config[deployment_section_name]["watsonx_url"] = os.getenv("WATSONX_URL", "")
    config[deployment_section_name]["space_id"] = os.getenv("WATSONX_SPACE_ID", "")
    config[deployment_section_name]["deployment_id"] = os.getenv("DEPLOYMENT_ID", "")

    # Map the same url for online parameters
    config[deployment_section_name]["online"]["parameters"]["url"] = config[deployment_section_name]["watsonx_url"]

    # TODO - consider changing sw_spec name with timestamp, as a temp solution set overwrite flag
    config[deployment_section_name]["software_specification"]["overwrite"] = True

    with open(target_file, "w") as f:
        f.write(dumps(config))


create_config(config_template, config_file)
