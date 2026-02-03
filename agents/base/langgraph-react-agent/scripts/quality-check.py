# Assisted by watsonx Code Assistant

# quality-check.py
import sys
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

# Add parent directory to Python path to import from utils.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils import load_config


# =========================
# Schemas
# =========================


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


# =========================
# Quality gate
# =========================

SCORE_THRESHOLD = 0.35


# =========================
# Helpers
# =========================


def retrieve_generated_answer(chat_completions: dict) -> str:
    """Extract the generated answer from the chat completion response."""
    return chat_completions["choices"][0]["message"]["content"]


def load_benchmarking_data(path: str) -> list[BenchmarkItemSchema]:
    """Load benchmarking data from a JSON Lines file.

    Args:
        benchmarking_data_path (str): Path to the JSON Lines file containing benchmark data.

    Returns:
        list[BenchmarkItemSchema]: List of benchmark items parsed from the file.
    """
    with open(path, "r") as f:
        return [json.loads(line) for line in f]


# =========================
# Generation
# =========================


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
            response = api_client.deployments.run_ai_service(
                deployment_id=deployment_id,
                ai_service_payload=payload,
            )

            results.append(retrieve_generated_answer(response))
            final_ids.append(payload_id)

        except Exception as e:
            raise RuntimeError(
                f"❌ Generation failed for sample {payload_id}: {e}"
            ) from e

    return final_ids, results


# =========================
# Evaluation
# =========================


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

    df = results.global_scores.to_df()
    print(df)

    return float(df.loc["score", "score"])


# =========================
# Main
# =========================

if __name__ == "__main__":
    # Load config and set deployment_id
    config = load_config("deployment")
    deployment_id = config["deployment_id"]

    # Init ibm_watsonx_ai.APIClient
    api_client = ibm_watsonx_ai.APIClient(
        credentials=ibm_watsonx_ai.Credentials(
            url=config["watsonx_url"],
            api_key=config["watsonx_apikey"],
        ),
        space_id=config["space_id"],
    )

    # benchmarking data are read from benchmarking_data d
    benchmarking_data_path = (
        Path(__file__).parents[1] / "benchmarking_data" / "benchmarking_data.jsonl"
    )

    benchmarking_data = load_benchmarking_data(str(benchmarking_data_path))

    # Executing deployed AI service with provided scoring data
    payloads_list: list[PayloadSchema] = [
        {"messages": [{"role": "user", "content": data["input"]}]}
        for data in benchmarking_data
    ]

    ids_list = [data["id"] for data in benchmarking_data]

    final_ids, answers = generate_answers(payloads_list, ids_list)

    # Safety check: never allow partial evaluation
    if len(final_ids) != len(ids_list):
        raise RuntimeError("❌ Not all benchmark samples produced predictions.")

    metrics = ["metrics.rouge", "metrics.bleu"]

    score = evaluate_agent(
        evaluation_data=benchmarking_data,
        predictions=answers,
        metrics=metrics,
    )

    print(f"\nFinal quality score: {score:.3f}")

    assert score >= SCORE_THRESHOLD, (
        f"❌ Quality gate failed: {score:.3f} < {SCORE_THRESHOLD}\n"
        f"Used metrics: {metrics}"
    )

    print("✅ Quality gate passed")
