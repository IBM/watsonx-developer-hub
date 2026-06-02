import os
from dotenv import load_dotenv
from typing import Literal
from pydantic import BaseModel, Field


class IrisInformation(BaseModel):
    sepal_length: float = Field(..., description="Sepal length in cm")
    sepal_width: float = Field(..., description="Sepal width in cm")
    petal_length: float = Field(..., description="Petal length in cm")
    species: Literal["setosa", "versicolor", "virginica"] = Field(
        ..., description="Iris species: setosa, versicolor, or virginica"
    )


def prepare_api_client():
    from ibm_watsonx_ai import APIClient, Credentials

    load_dotenv()

    api_client = APIClient(
        credentials=Credentials(
            url=os.getenv("WATSONX_URL"),
            api_key=os.getenv("WATSONX_API_KEY"),
        ),
        space_id=os.getenv("WATSONX_SPACE_ID"),
    )
    return api_client


def get_petal_width_deployment_id() -> str:
    load_dotenv()
    deployment_id = os.getenv("WATSONX_PETAL_WIDTH_DEPLOYMENT_ID")
    if not deployment_id:
        raise ValueError("WATSONX_PETAL_WIDTH_DEPLOYMENT_ID is not set")
    return deployment_id


def build_scoring_payload(iris: IrisInformation) -> dict:
    """Build the scoring payload in the format expected by watsonx.ai deployment."""
    return {
        "input_data": [
            {
                "fields": ["sepal_length", "sepal_width", "petal_length", "species"],
                "values": [
                    [
                        iris.sepal_length,
                        iris.sepal_width,
                        iris.petal_length,
                        iris.species,
                    ]
                ],
            }
        ]
    }


def extract_petal_width(response: dict) -> float:
    """Extract the predicted petal width float from the watsonx.ai scoring response."""
    try:
        predictions = response["predictions"][0]
        values = predictions["values"][0]
        # The deployment returns a list of predicted values; petal width is the first
        return float(values[0])
    except (KeyError, IndexError, TypeError, ValueError) as e:
        raise RuntimeError(f"Unexpected response structure from deployment: {response}") from e