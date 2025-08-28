import tomllib
from pathlib import Path
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
        }
        config["deployment"].update(dotenv_data)
    if section is not None:
        return config[section]
    else:
        return config