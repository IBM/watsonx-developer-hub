# Assisted by watsonx Code Assistant

# quality-check.py
import json
from pathlib import Path
import warnings
from typing import TypedDict, Literal, Sequence

# catch warning `pkg_resources is deprecated as an API. ...` from unitxt.operator.py
with warnings.catch_warnings(category=UserWarning):
    warnings.filterwarnings("ignore")
    from unitxt.api import create_dataset, evaluate  # type: ignore[import-untyped]
    from unitxt.blocks import Task, InputOutputTemplate  # type: ignore[import-untyped]

import ibm_watsonx_ai  # type: ignore[import-untyped]
from utils import load_config


# Define schema for message, payload, and benchmark item structures
class MessageSchema(TypedDict):
    """Schema for a message in a conversation, specifying its role and content."""

    role: Literal["system", "user"]
    content: str


class PayloadSchema(TypedDict):
    """Schema for a payload containing a list of messages."""

    messages: list[MessageSchema]


class BenchmarkItemSchema(TypedDict):
    """Schema for a benchmark item containing an ID, payload, and correct answer."""

    id: str
    input: str
    ground_truth: str


# Default threshold for evaluation score
SCORE_THRESHOLD = 0.5


# Helper functions
def retrieve_generated_answer(chat_completions: dict) -> str:
    """Extract the generated answer from the chat completion response."""
    return chat_completions["choices"][0]["message"]["content"]


def load_benchmarking_data(benchmarking_data_path: str) -> list[BenchmarkItemSchema]:
    """Load benchmarking data from a JSON Lines file.

    Args:
        benchmarking_data_path (str): Path to the JSON Lines file containing benchmark data.

    Returns:
        list[BenchmarkItemSchema]: List of benchmark items parsed from the file.
    """
    with open(benchmarking_data_path, "r") as f:
        benchmarking_data = [json.loads(line) for line in f]

    return benchmarking_data


def generate_answers(
    input_data: Sequence[PayloadSchema], ids: list[str]
) -> tuple[list[str], list[str]]:
    """Generate answers using the deployed AI service for given input data.

    Args:
        input_data (Sequence[PayloadSchema]): List of payloads containing messages.
        ids (list[str]): List of IDs corresponding to the payloads.

    Returns:
        (list[str], list[str]): Tuples of final IDs and generated answers.
    """
    results = []
    final_ids = []

    for payload, payload_id in zip(input_data, ids):
        try:
            results.append(
                retrieve_generated_answer(
                    api_client.deployments.run_ai_service(
                        deployment_id=deployment_id, ai_service_payload=payload
                    )
                )
            )
            final_ids.append(payload_id)
        except Exception as e:
            warnings.warn(f"Skipping sample: {payload_id}. Reason: {e}")

    return final_ids, results


def evaluate_agent(
    evaluation_data: list[BenchmarkItemSchema],
    predictions: list[str],
    metrics: list[str],
) -> float:
    """Evaluate the agent's performance using provided metrics.

    Args:
        evaluation_data (list[BenchmarkItemSchema]): List of benchmark items for evaluation.
        predictions (list[str]): List of generated answers.
        metrics (list[str]): List of evaluation metrics to use.

    Returns:
        float: The evaluation score.
    """
    dataset = [
        {
            "question": record["input"],
            "answer": record["ground_truth"],
            "system_prompt": (
                first_message
                if (first_message := record.get("system_prompt")) == "system"
                else ""
            ),
        }
        for record in evaluation_data
    ]

    # Define the task and evaluation metric
    task = Task(
        input_fields={"question": str, "system_prompt": str},
        reference_fields={"answer": str},
        prediction_type=str,
        metrics=metrics,
    )

    # Create a template to format inputs and outputs
    template = InputOutputTemplate(
        instruction="{system_prompt}",
        input_format="{question}",
        output_format="{answer}",
        postprocessors=["processors.lower_case"],
    )

    dataset = create_dataset(
        task=task,
        template=template,
        format="formats.chat_api",
        test_set=dataset,
        split="test",
    )

    results = evaluate(predictions=predictions, dataset=dataset)

    df_results = results.global_scores.to_df()
    print(df_results)

    return df_results.to_dict().get("score", {}).get("score", 0)


if __name__ == "__main__":
    # Load config and set deployment_id
    config = load_config("deployment")
    deployment_id = config["deployment_id"]

    # Init ibm_watsonx_ai.APIClient
    api_client = ibm_watsonx_ai.APIClient(
        credentials=ibm_watsonx_ai.Credentials(
            url=config["watsonx_url"], api_key=config["watsonx_apikey"]
        ),
        space_id=config["space_id"],
    )

    # Load benchmarking data
    benchmarking_filename = "benchmarking_data.jsonl"

    # benchmarking data are read from benchmarking_data dir
    benchmarking_data_dir = Path("benchmarking_data")
    benchmarking_data_path = (
        Path(__file__).parents[1] / benchmarking_data_dir / benchmarking_filename
    )

    benchmarking_data = load_benchmarking_data(
        benchmarking_data_path=str(benchmarking_data_path)
    )

    # Executing deployed AI service with provided scoring data
    payloads_list: list[PayloadSchema] = [
        {"messages": [{"role": "user", "content": data["input"]}]}
        for data in benchmarking_data
    ]
    correct_answer_list = [data["ground_truth"] for data in benchmarking_data]
    ids_list = [data["id"] for data in benchmarking_data]

    final_ids, answers = generate_answers(payloads_list, ids_list)

    metrics = ["metrics.rouge", "metrics.bleu"]

    # Check whether QA metric score is larger than acceptable threshold
    assert (
        evaluate_agent(
            evaluation_data=[
                _data for _data in benchmarking_data if _data["id"] in final_ids
            ],
            predictions=answers,
            metrics=metrics,
        )
        > SCORE_THRESHOLD
    ), f"Agent does not pass quality check. Used metrics: {metrics}, threshold: {SCORE_THRESHOLD}"
