import os
from dotenv import load_dotenv


def prepare_api_client():
    from ibm_watsonx_ai import APIClient, Credentials

    load_dotenv()

    api_client = APIClient(
        credentials=Credentials(
            url=os.getenv("WATSONX_URL"), api_key=os.getenv("WATSONX_API_KEY")
        ),
        space_id=os.getenv("WATSONX_SPACE_ID"),
    )
    return api_client


def prepare_chat_watsonx():
    from langchain_ibm import ChatWatsonx

    api_client = prepare_api_client()

    chat_watsonx = ChatWatsonx(
        model_id=os.getenv("WATSONX_MODEL_ID"),
        watsonx_client=api_client,
    )
    return chat_watsonx


def get_credit_risk_deployment_id():
    load_dotenv()
    return os.getenv("WATSONX_CREDIT_RISK_DEPLOYMENT_ID")


def format_output_to_metadata(output_obj):
    fields = [
        "CheckingStatus",
        "LoanDuration",
        "CreditHistory",
        "LoanPurpose",
        "LoanAmount",
        "ExistingSavings",
        "EmploymentDuration",
        "InstallmentPercent",
        "Sex",
        "OthersOnLoan",
        "CurrentResidenceDuration",
        "OwnsProperty",
        "Age",
        "InstallmentPlans",
        "Housing",
        "ExistingCreditsCount",
        "Job",
        "Dependents",
        "Telephone",
        "ForeignWorker",
    ]

    values = [getattr(output_obj, field) for field in fields]

    metadata = {"input_data": [{"fields": fields, "values": [values]}]}

    return metadata
