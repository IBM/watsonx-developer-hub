from datetime import datetime, timedelta, timezone
import logging
import os
import time
from typing import Literal
import warnings
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai.wml_client_error import WMLClientError

ContainerType = Literal["project", "space"]

CONTAINER_NAME_PREFIX = "watsonx_developer_hub_test"
logger = logging.getLogger(__name__)


def _get_container_name(container_type: ContainerType) -> str:
    now = datetime.now(tz=timezone.utc).isoformat()
    return f"{CONTAINER_NAME_PREFIX}_{container_type}_{now}"


def delete_container(
    api_client: APIClient,
    container_type: ContainerType,
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
        warnings.warn(
            f"{container_type.capitalize()} cannot be deleted due to the error: {e}"
        )

    # Wait for container deletion to complete
    time.sleep(10)

    api_client.default_project_id = api_client.default_space_id = None


def delete_old_containers(api_client: APIClient, container_type: ContainerType) -> None:
    delete_threshold = datetime.now(tz=timezone.utc) - timedelta(days=0)

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
            delete_container(api_client, container_type, container_id, container_name)


def create_new_space(api_client: APIClient) -> tuple[str, str]:
    space_name = _get_container_name("space")

    metadata = {
        api_client.spaces.ConfigurationMetaNames.NAME: space_name,
        api_client.spaces.ConfigurationMetaNames.STORAGE: {
            "type": "bmcos_object_storage",
            "resource_crn": os.environ["COS_RESOURCE_INSTANCE_ID"],
        },
        api_client.spaces.ConfigurationMetaNames.COMPUTE: {
            "name": os.environ["WATSONX_COMPUTE_NAME"],
            "crn": os.environ["WATSONX_IAM_SERVICE_ID_CRN"],
        },
        api_client.spaces.ConfigurationMetaNames.TYPE: "wx",
    }

    space_details = api_client.spaces.store(meta_props=metadata, background_mode=False)
    space_id = api_client.spaces.get_id(space_details)

    logger.info("New space '%s' has been created, space_id=%s", space_name, space_id)

    # Wait for space creation to complete
    time.sleep(5)

    return space_id, space_name


def create_new_project(api_client: APIClient) -> tuple[str, str]:
    project_name = _get_container_name("project")

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
            "name": os.environ["WATSONX_COMPUTE_NAME"],
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

    return project_id, project_name
