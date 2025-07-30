import tomllib
from pathlib import Path
from ibm_watsonx_ai import APIClient

def load_config(section: str | None = None) -> dict:
    config = tomllib.loads((Path(__file__).parent / "config.toml").read_text())
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