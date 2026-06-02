from mcp.server.fastmcp import FastMCP
from utils import (
    IrisInformation,
    prepare_api_client,
    get_petal_width_deployment_id,
    build_scoring_payload,
    extract_petal_width,
)

mcp = FastMCP("iris-toolkit")
api_client = prepare_api_client()


@mcp.tool()
def get_petal_width_from_iris_data(iris_information: IrisInformation) -> float:
    """
    Predict the petal width (in cm) of an iris flower using a watsonx.ai deployed model.

    Provide sepal_length, sepal_width, petal_length (all in cm as floats),
    and species (one of: setosa, versicolor, virginica).

    Returns the predicted petal width as a float.
    """
    deployment_id = get_petal_width_deployment_id()
    payload = build_scoring_payload(iris_information)
    response = api_client.deployments.score(deployment_id, meta_props=payload)
    return extract_petal_width(response)


if __name__ == "__main__":
    mcp.run(transport="stdio")