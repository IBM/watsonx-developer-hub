from datetime import datetime
import logging
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Generator, cast
import pytest

from ibm_watsonx_ai import Credentials, APIClient
from ibm_watsonx_ai.deployment import WebService
from ibm_watsonx_ai.experiment import AutoAI
from ibm_watsonx_ai.experiment.autoai.optimizers import RemoteAutoPipelines
from ibm_watsonx_ai.helpers import DataConnection, ContainerLocation
from ibm_watsonx_ai.foundation_models.utils import VectorIndexes
from ibm_watsonx_ai.foundation_models.embeddings import Embeddings
from ibm_watsonx_ai.foundation_models.extensions.rag import VectorStore

from container_utils import (
    create_new_project,
    create_new_space,
    delete_old_containers,
    delete_container,
)


logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", name="context_free_api_client")
def fixture_context_free_api_client() -> APIClient:
    credentials = Credentials(
        url=os.environ["WATSONX_URL"], api_key=os.environ["WATSONX_API_KEY"]
    )

    return APIClient(credentials)


@pytest.fixture(scope="session", name="space_id")
def fixture_space_id(context_free_api_client: APIClient) -> Generator[str, None, None]:
    if space_id := os.environ.get("WATSONX_SPACE_ID"):
        yield space_id
        return

    delete_old_containers(context_free_api_client, "space")

    space_id, space_name = create_new_space(context_free_api_client)

    mp = pytest.MonkeyPatch()
    mp.setenv("WATSONX_SPACE_ID", space_id)

    yield space_id

    mp.undo()
    delete_container(context_free_api_client, "space", space_id, space_name)


@pytest.fixture(scope="session", name="project_id")
def fixture_project_id(
    context_free_api_client: APIClient,
) -> Generator[str, None, None]:
    if project_id := os.environ.get("WATSONX_PROJECT_ID"):
        yield project_id
        return

    delete_old_containers(context_free_api_client, "project")

    project_id, project_name = create_new_project(context_free_api_client)

    yield project_id

    delete_container(context_free_api_client, "project", project_id, project_name)


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


@pytest.fixture(name="tmp_dir")
def fixture_tmp_dir() -> Generator[str, None, None]:
    with TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture(name="test_venv_path")
def fixture_test_venv_path() -> Path:
    venv_name = ".venv_test"
    version = sys.version.split(" ", 1)[0]

    subprocess.run(
        [Path(__file__).parent / "create_test_venv_with_uv.sh", venv_name, version],
        check=True,
    )

    return Path(__file__).parents[1] / venv_name


@pytest.fixture(scope="session", name="psql_connection_id")
def fixture_psql_connection_id(space_api_client: APIClient) -> str:
    if psql_connection_id := os.environ.get("WATSONX_PSQL_CONNECTION_ID"):
        return psql_connection_id

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
    if milvus_connection_id := os.environ.get("WATSONX_MILVUS_CONNECTION_ID"):
        return milvus_connection_id

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
        project_api_client.foundation_models.EmbeddingModels.SLATE_125M_ENGLISH_RTRVR_V2  # type: ignore
    )

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


@pytest.fixture(scope="session", name="credit_risk_deployment_id")
def fixture_credit_risk_deployment_id(
    space_api_client: APIClient,
) -> Generator[str, None, None]:
    if credit_risk_deployment_id := os.environ.get("WATSONX_CREDIT_RISK_DEPLOYMENT_ID"):
        yield credit_risk_deployment_id
        return

    credit_risk_connection = DataConnection(ContainerLocation("credit_risk_light.csv"))
    credit_risk_connection.set_client(space_api_client)
    credit_risk_connection.write(
        Path(__file__).parent / "data" / "credit_risk_training_light.csv"
    )

    experiment = AutoAI(
        space_api_client.credentials, space_id=space_api_client.default_space_id
    )

    pipeline_optimizer = experiment.optimizer(
        name="Credit Risk Prediction and bias detection - AutoAI",
        prediction_type=AutoAI.PredictionType.BINARY,  # type: ignore
        prediction_column="Risk",
        scoring=AutoAI.Metrics.ROC_AUC_SCORE,  # type: ignore
    )
    pipeline_optimizer = cast(RemoteAutoPipelines, pipeline_optimizer)

    # pylint: disable=no-value-for-parameter,unexpected-keyword-arg
    run_details = pipeline_optimizer.fit(
        training_data_reference=[credit_risk_connection]
    )

    run_id = run_details["metadata"]["id"]

    assert pipeline_optimizer.get_run_status() == "completed"

    service = WebService(
        space_api_client.credentials, source_space_id=space_api_client.default_space_id
    )
    service.create(
        next(iter(pipeline_optimizer.summary().index)),
        "Credit Risk Deployment AutoAI",
        experiment_run_id=run_id,
    )

    assert service.id is not None, "Service ID should be set after deployment"

    # Created during the fit process
    os.remove("request.json")

    yield service.id

    service.delete()
