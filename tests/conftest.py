from datetime import datetime, timezone, timedelta
import os
from tempfile import TemporaryDirectory
import time
from typing import Generator
from warnings import warn
import pytest

from ibm_watsonx_ai import Credentials, APIClient
from ibm_watsonx_ai.wml_client_error import WMLClientError


SPACE_NAME_PREFIX = "watsonx_developer_hub_test_space"
OS_VARS_MAPPING = {
    "WATSONX_APIKEY": "WX_API_KEY",  # pragma: allowlist secret
    "WATSONX_URL": "WX_URL",
}


def _delete_space(api_client: APIClient, space_id: str, space_name: str) -> None:
    print(f"Deleting old space '{space_name}' with ID {space_id}")

    api_client.set.default_space(space_id)
    deployments = api_client.deployments.get_details()["resources"]

    try:
        for deployment in deployments:
            api_client.deployments.delete(deployment["metadata"]["id"])

        space_details = api_client.spaces.get_details(space_id)
        api_client.spaces.delete(space_id)

        space_name = space_details["entity"]["name"]
        print(f"Deleted space '{space_name}' with ID {space_id}")
    except WMLClientError as e:
        warn(f"Space cannot be deleted due to the error: {e}")

    # Wait for space deletion to complete
    time.sleep(10)


def _delete_old_spaces(api_client: APIClient) -> None:
    delete_threshold = datetime.now(tz=timezone.utc) - timedelta(days=0) # TODO: increase after tests

    for _, row in api_client.spaces.list().iterrows():
        space_id = str(row["ID"])
        space_name = str(row["NAME"])
        space_creation_time = datetime.fromisoformat(str(row["CREATED"]))

        if (
            space_name.startswith(SPACE_NAME_PREFIX)
            and space_creation_time <= delete_threshold
        ):
            _delete_space(api_client, space_id, space_name)


def _create_new_space(api_client: APIClient, space_name: str):
    metadata = {
        api_client.spaces.ConfigurationMetaNames.NAME: space_name,
        api_client.spaces.ConfigurationMetaNames.STORAGE: {
            "type": "bmcos_object_storage",
            "resource_crn": os.environ["COS_RESOURCE_INSTANCE_ID"],
        },
        api_client.spaces.ConfigurationMetaNames.COMPUTE: {
            "name": os.environ["WX_NAME"],
            "crn": os.environ["WX_IAM_SERVICE_ID_CRN"],
        },
        api_client.spaces.ConfigurationMetaNames.TYPE: "wx",
    }

    space_details = api_client.spaces.store(meta_props=metadata, background_mode=False)
    space_id = api_client.spaces.get_id(space_details)

    print(f"New space `{space_name}` has been created, space_id={space_id}")

    # Wait for space creation to complete
    time.sleep(5)

    return space_id


@pytest.fixture(scope="session", name="context_free_api_client")
def fixture_context_free_api_client() -> APIClient:
    credentials = Credentials(
        url=os.environ["WX_URL"], api_key=os.environ["WX_API_KEY"]
    )

    return APIClient(credentials)


@pytest.fixture(scope="session", name="space_id")
def fixture_space_id(context_free_api_client: APIClient) -> Generator[str, None, None]:
    _delete_old_spaces(context_free_api_client)

    now = datetime.now(tz=timezone.utc).isoformat()
    space_name = f"{SPACE_NAME_PREFIX}_{now}"

    space_id = _create_new_space(context_free_api_client, space_name)

    yield space_id

    _delete_space(context_free_api_client, space_id, space_name)


@pytest.fixture(scope="session", name="env_file_values")
def fixture_env_file_values(space_id: str) -> dict[str, str]:
    env_values = {
        cli: os.environ[env]
        for cli, env in OS_VARS_MAPPING.items()
    }
    env_values["WATSONX_SPACE_ID"] = space_id

    return env_values


@pytest.fixture(scope="session", name="tmp_dir")
def fixture_tmp_dir() -> Generator[str, None, None]:
    with TemporaryDirectory() as tmp_dir:
        yield tmp_dir
