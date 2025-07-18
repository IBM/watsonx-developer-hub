import tomllib
from pathlib import Path
from ibm_watsonx_ai import APIClient
from dotenv import load_dotenv
import os

def load_dotenv_with_current_path() -> None:
    """
    Load environment variables from a `.env` file in the current working directory.
    """
    dotenv_path = Path.cwd() / ".env"

    if not dotenv_path.is_file():
        raise FileNotFoundError(".env was not found or is a directory")

    load_dotenv(dotenv_path=dotenv_path, verbose=True, override=True)


def get_from_env(env_key: str) -> str | None:
    value = os.environ.get(env_key, "").strip()
    return value

def load_config(section: str | None = None) -> dict:

    dotenv_exists = True
    try:
        load_dotenv_with_current_path()
    except FileNotFoundError:
        dotenv_exists = False

    config = tomllib.loads((Path(__file__).parent / "config.toml").read_text())
    if dotenv_exists:
        dotenv_data = {
            "watsonx_apikey": get_from_env("WATSONX_APIKEY"),
            "watsonx_url": get_from_env("WATSONX_URL"),
            "watsonx_token": get_from_env("WATSONX_TOKEN"),
            "space_id": get_from_env("WATSONX_SPACE_ID"),
            "deployment_id": get_from_env("WATSONX_DEPLOYMENT_ID"),
            "watsonx_password": get_from_env("WATSONX_PASSWORD"),
            "watsonx_username": get_from_env("WATSONX_USERNAME"),
            "watsonx_instance_id": get_from_env("WATSONX_INSTANCE_ID"),
        }
        config["deployment"].update(dotenv_data)
    if section is not None:
        return config[section]
    else:
        return config


def generate_database_URI(client: APIClient, postgres_db_conenction_id: str):
    db_details = client.connections.get_details(postgres_db_conenction_id)
    db_credentials = db_details["entity"]["properties"]
    db_host = db_credentials["host"]
    db_port = db_credentials["port"]
    db_name = db_credentials["database"] 
    db_username = db_credentials["username"]
    db_password = db_credentials["password"]
    return f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"