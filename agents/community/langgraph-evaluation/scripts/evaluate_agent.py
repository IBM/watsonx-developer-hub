from prebuilt_agent import make_agent
import pandas as pd
from pathlib import Path

from utils import load_config
from ibm_watsonx_ai import APIClient, Credentials

from ibm_watsonx_gov.config import GenAIConfiguration
from ibm_watsonx_gov.entities.enums import TaskType
from ibm_watsonx_gov.evaluators import MetricsEvaluator
from ibm_watsonx_gov.metrics.answer_relevance.answer_relevance_metric import AnswerRelevanceMetric
from ibm_watsonx_gov.metrics.answer_similarity.answer_similarity_metric import AnswerSimilarityMetric
import os

def metrics_to_dataframe(metrics: list):
    rows = []
    for m in metrics:
        threshold = m.thresholds[0].value if m.thresholds else None
        for rec in m.record_level_metrics:
            rows.append({
                "metric_name": m.name,
                "method": m.method,
                "provider": m.provider,
                "record_id": rec.record_id,
                "value": rec.value,
                "threshold": threshold,
                "status": "ok" if rec.value >= threshold else "below"
            })
    return pd.DataFrame(rows)
                        
BASE_DIR = Path(__file__).parent.resolve()
evaluation_data = BASE_DIR / "example_evaluation_data.csv" 
data_with_answers = BASE_DIR / "data_with_answers.csv"
metrics_results_data = BASE_DIR / "metric_results.csv"


config = load_config()
dep_config = config["deployment"]
online_parameters = dep_config["online"]["parameters"]

client = APIClient(
    credentials=Credentials(
        url=dep_config["watsonx_url"], api_key=dep_config["watsonx_apikey"]
    ),
    space_id=dep_config["space_id"],
)

agent = make_agent(client, online_parameters["model_id"])
data = pd.read_csv(evaluation_data)

config = GenAIConfiguration(
        input_fields=["question"],
        output_fields=["answer"],
        reference_fields=["ground_truth"],
        task_type=TaskType.QA
    )

os.environ["WATSONX_APIKEY"] = dep_config["watsonx_apikey"]

evaluator = MetricsEvaluator(configuration=config)

answers = []
for question in data["question"]:
    resposne = agent.invoke({"messages": question})
    answers.append(resposne["messages"][-1].content)

data["answer"] = answers
data.to_csv(data_with_answers, index=False)

metrics = [
        AnswerSimilarityMetric(),
        AnswerRelevanceMetric(),
    ]

result = evaluator.evaluate(data=data, metrics=metrics)
for r in result.metrics_result:
    print(r.model_dump_json(indent=2))
    print("\n\n\n")

df = metrics_to_dataframe(result.metrics_result)
df.to_csv(metrics_results_data, index=False)