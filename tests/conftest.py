from datetime import datetime, timezone, timedelta
import logging
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import time
from typing import Generator, Literal
from warnings import warn
import pytest

from ibm_watsonx_ai import Credentials, APIClient
from ibm_watsonx_ai.wml_client_error import WMLClientError
from ibm_watsonx_ai.foundation_models.utils import VectorIndexes
from ibm_watsonx_ai.foundation_models.embeddings import Embeddings
from ibm_watsonx_ai.foundation_models.extensions.rag import VectorStore

CONTAINER_NAME_PREFIX = "watsonx_developer_hub_test"


logger = logging.getLogger(__name__)


def _delete_container(
    api_client: APIClient,
    container_type: Literal["project", "space"],
    container_id: str,
    container_name: str,
) -> None:
    logger.info(
        "Deleting old %s '%s' with ID %s", container_type, container_name, container_id
    )

    if container_type == "project":
        api_client.set.default_project(container_id)
    else:
        api_client.set.default_space(container_id)

    try:
        deployments = api_client.deployments.get_details()["resources"]

        for deployment in deployments:
            api_client.deployments.delete(deployment["metadata"]["id"])

        if container_type == "project":
            api_client.projects.delete(container_id)
        else:
            api_client.spaces.delete(container_id)

        logger.info(
            "Deleted %s '%s' with ID %s", container_type, container_name, container_id
        )
    except WMLClientError as e:
        warn(f"{container_type.capitalize()} cannot be deleted due to the error: {e}")

    # Wait for container deletion to complete
    time.sleep(10)

    api_client.default_project_id = api_client.default_space_id = None


def _delete_old_containers(api_client: APIClient) -> None:
    delete_threshold = datetime.now(tz=timezone.utc) - timedelta(days=0)

    for container_type in ("project", "space"):
        if container_type == "project":
            container_df = api_client.projects.list()
        else:
            container_df = api_client.spaces.list()

        for _, row in container_df.iterrows():
            container_id = str(row["ID"])
            container_name = str(row["NAME"])
            container_creation_time = datetime.fromisoformat(str(row["CREATED"]))

            if (
                container_name.startswith(CONTAINER_NAME_PREFIX)
                and container_creation_time <= delete_threshold
            ):
                _delete_container(
                    api_client, container_type, container_id, container_name
                )


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

    logger.info("New space '%s' has been created, space_id=%s", space_name, space_id)

    # Wait for space creation to complete
    time.sleep(5)

    return space_id


def _create_new_project(api_client: APIClient, project_name: str) -> str:
    storage_guid = (
        os.environ["COS_RESOURCE_INSTANCE_ID"].replace("::", "").split(":")[-1]
    )
    compute_guid = os.environ["WX_IAM_SERVICE_ID_CRN"].replace("::", "").split(":")[-1]

    meta_props = {
        api_client.projects.ConfigurationMetaNames.NAME: project_name,
        api_client.projects.ConfigurationMetaNames.GENERATOR: "wx-registration-sandbox",
        api_client.projects.ConfigurationMetaNames.STORAGE: {
            "type": "bmcos_object_storage",
            "resource_crn": os.environ["COS_RESOURCE_INSTANCE_ID"],
            "guid": storage_guid,
        },
        api_client.projects.ConfigurationMetaNames.COMPUTE: {
            "type": "machine_learning",
            "name": os.environ["WX_NAME"],
            "crn": os.environ["WX_IAM_SERVICE_ID_CRN"],
            "guid": compute_guid,
        },
        api_client.projects.ConfigurationMetaNames.TYPE: "wx",
        api_client.projects.ConfigurationMetaNames.PUBLIC: False,
    }

    project_details = api_client.projects.store(meta_props)
    project_id = api_client.projects.get_id(project_details)

    logger.info(
        "New project '%s' has been created, project_id=%s", project_name, project_id
    )

    return project_id


@pytest.fixture(scope="session", name="context_free_api_client")
def fixture_context_free_api_client() -> APIClient:
    credentials = Credentials(
        url=os.environ["WX_URL"], api_key=os.environ["WX_API_KEY"]
    )

    return APIClient(credentials)


@pytest.fixture(scope="session", name="space_id")
def fixture_space_id(context_free_api_client: APIClient) -> Generator[str, None, None]:
    _delete_old_containers(context_free_api_client)

    now = datetime.now(tz=timezone.utc).isoformat()
    space_name = f"{CONTAINER_NAME_PREFIX}_space_{now}"

    space_id = _create_new_space(context_free_api_client, space_name)

    mp = pytest.MonkeyPatch()
    mp.setenv("WATSONX_SPACE_ID", space_id)

    yield space_id

    mp.undo()
    _delete_container(context_free_api_client, "space", space_id, space_name)


@pytest.fixture(scope="session", name="project_id")
def fixture_project_id(
    context_free_api_client: APIClient,
) -> Generator[str, None, None]:
    now = datetime.now(tz=timezone.utc).isoformat()
    project_name = f"{CONTAINER_NAME_PREFIX}_project_{now}"

    project_id = _create_new_project(context_free_api_client, project_name)

    yield project_id

    _delete_container(context_free_api_client, "project", project_id, project_name)


@pytest.fixture(scope="session", name="space_api_client")
def fixture_space_api_client(
    context_free_api_client: APIClient, space_id: str
) -> APIClient:
    api_client = context_free_api_client.get_copy()
    api_client.set_token(context_free_api_client.token)
    api_client.set.default_space(space_id)
    return api_client


@pytest.fixture(scope="session", name="project_api_client")
def fixture_project_api_client(
    context_free_api_client: APIClient, project_id: str
) -> APIClient:
    api_client = context_free_api_client.get_copy()
    api_client.set_token(context_free_api_client.token)
    api_client.set.default_project(project_id)
    return api_client


@pytest.fixture(scope="session", name="env_file_values")
def fixture_env_file_values(space_id: str) -> dict[str, str]:
    os_vars_mapping = {
        "WATSONX_APIKEY": "WX_API_KEY",  # pragma: allowlist secret
        "WATSONX_URL": "WX_URL",
    }

    env_values = {cli: os.environ[env] for cli, env in os_vars_mapping.items()}
    env_values["WATSONX_SPACE_ID"] = space_id

    return env_values


@pytest.fixture(name="tmp_dir")
def fixture_tmp_dir() -> Generator[str, None, None]:
    with TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture(name="test_venv_path")
def fixture_test_venv_path() -> Path:
    venv_name = ".venv_test"

    subprocess.run(
        [Path(__file__).parent / "create_test_venv_with_uv.sh", venv_name, "3.11"],
        check=True,
    )

    return Path(__file__).parents[1] / venv_name


@pytest.fixture(scope="session", name="psql_connection_id")
def fixture_psql_connection_id(space_api_client: APIClient) -> str:
    datasource_type = space_api_client.connections.get_datasource_type_id_by_name(
        "postgresql-ibmcloud"
    )

    meta_props = {
        space_api_client.connections.ConfigurationMetaNames.DATASOURCE_TYPE: datasource_type,
        space_api_client.connections.ConfigurationMetaNames.NAME: "PostgreSQL connection",
        space_api_client.connections.ConfigurationMetaNames.PROPERTIES: {
            "host": os.environ["PSQL_HOST"],
            "port": os.environ["PSQL_PORT"],
            "database": os.environ["PSQL_DATABASE"],
            "username": os.environ["PSQL_USERNAME"],
            "password": os.environ["PSQL_PASSWORD"],
        },
    }

    connection_details = space_api_client.connections.create(meta_props)
    return space_api_client.connections.get_id(connection_details)


@pytest.fixture(scope="session", name="project_milvus_connection_id")
def fixture_project_milvus_connection_id(project_api_client: APIClient) -> str:
    datasource_type = project_api_client.connections.get_datasource_type_id_by_name(
        "milvuswxd"
    )

    meta_props = {
        project_api_client.connections.ConfigurationMetaNames.DATASOURCE_TYPE: datasource_type,
        project_api_client.connections.ConfigurationMetaNames.NAME: "Milvus connection",
        project_api_client.connections.ConfigurationMetaNames.PROPERTIES: {
            "host": os.environ["MILVUS_HOST"],
            "port": os.environ["MILVUS_PORT"],
            "username": os.environ["MILVUS_USERNAME"],
            "password": os.environ["MILVUS_PASSWORD"],
            "ssl": True,
        },
    }

    connection_details = project_api_client.connections.create(meta_props)
    return project_api_client.connections.get_id(connection_details)


@pytest.fixture(scope="session", name="project_vector_index_id")
def fixture_project_vector_index_id(
    project_api_client: APIClient, project_milvus_connection_id: str
) -> str:
    index_name = f"watsonxdeveloperhubindex{int(datetime.now().timestamp())}"
    database_name = "default"
    embedding_model_id = (
        project_api_client.foundation_models.EmbeddingModels.SLATE_125M_ENGLISH_RTRVR_V2
    )  # type: ignore

    vector_indexes = VectorIndexes(project_api_client)
    vector_index_details = vector_indexes.create(
        name=f"vector_index_{datetime.now().isoformat()}",
        store={
            "type": "watsonx.data",
            "connection_id": project_milvus_connection_id,
            "index": index_name,
            "database": database_name,
        },
        settings={
            "chunk_size": 2000,
            "chunk_overlap": 200,
            "split_pdf_pages": True,
            "top_k": 5,
            "rerank": False,
            "embedding_model_id": embedding_model_id,
            "schema_fields": {
                "document_name": "document_name",
                "text": "text",
                "page_number": "page",
            },
        },
    )

    embeddings = Embeddings(model_id=embedding_model_id, api_client=project_api_client)

    vector_store = VectorStore(
        project_api_client,
        connection_id=project_milvus_connection_id,
        index_name=index_name,
        database=database_name,
        embeddings=embeddings,
    )
    vector_store.add_documents(["Example document"])

    return vector_index_details["id"]


@pytest.fixture(scope="session", name="vector_index_id")
def fixture_vector_index_id(
    context_free_api_client: APIClient,
    project_vector_index_id: str,
    project_id: str,
    space_id: str,
) -> str:
    return context_free_api_client.spaces.promote(
        project_vector_index_id, project_id, space_id
    )
