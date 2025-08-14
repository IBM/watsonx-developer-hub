import json
from pathlib import Path
from typing import Any
import requests

DATASET_URL = (
    "https://datasets-server.huggingface.co/rows"
    "?dataset=rag-datasets%2Frag-mini-wikipedia"
    "&config=question-answer"
    "&split=test"
)
BATCH_SIZE = 100
TOTAL_ROWS = 918
OUTPUT_FILE = Path("benchmarking_data/benchmarking_data.jsonl")


def prepare_data(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in data:
        row_idx = row.get("row_idx")
        row_content = row.get("row")
        prepared_row = {
            "id": row_idx,
            "input": row_content.get("question"),
            "ground_truth": [row_content.get("answer")],
        }
        result.append(prepared_row)
    return result


def fetch_dataset(offset: int, length: int) -> list[dict[str, Any]]:
    response = requests.get(f"{DATASET_URL}&offset={offset}&length={length}", timeout=10)
    response.raise_for_status()
    rows = response.json().get("rows", [])
    return prepare_data(rows)


evaluation_data: list[dict[str, Any]] = []

for offset in range(0, TOTAL_ROWS, BATCH_SIZE):
    batch = fetch_dataset(offset, BATCH_SIZE)
    evaluation_data.extend(batch)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT_FILE.open("w", encoding="utf-8") as f:
    for record in evaluation_data:
        json.dump(record, f, ensure_ascii=False)
        f.write("\n")
