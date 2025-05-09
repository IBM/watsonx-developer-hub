import os
from dotenv import load_dotenv
from typing import Literal
from pydantic import BaseModel


class PersonInformation(BaseModel):
    CheckingStatus: Literal["0_to_200", "less_0", "no_checking", "greater_200"]
    LoanDuration: float
    CreditHistory: Literal[
        "credits_paid_to_date",
        "prior_payments_delayed",
        "outstanding_credit",
        "all_credits_paid_back",
        "no_credits",
    ]
    LoanPurpose: Literal[
        "other",
        "car_new",
        "furniture",
        "retraining",
        "education",
        "vacation",
        "appliances",
        "car_used",
        "repairs",
        "radio_tv",
        "business",
    ]
    LoanAmount: float
    ExistingSavings: Literal[
        "100_to_500", "less_100", "500_to_1000", "unknown", "greater_1000"
    ]
    EmploymentDuration: Literal["less_1", "1_to_4", "greater_7", "4_to_7", "unemployed"]
    InstallmentPercent: float
    Sex: Literal["female", "male"]
    OthersOnLoan: Literal["none", "co-applicant", "guarantor"]
    CurrentResidenceDuration: float
    OwnsProperty: Literal["savings_insurance", "real_estate", "unknown", "car_other"]
    Age: float
    InstallmentPlans: Literal["none", "stores", "bank"]
    Housing: Literal["own", "free", "rent"]
    ExistingCreditsCount: float
    Job: Literal["skilled", "management_self-employed", "unskilled", "unemployed"]
    Dependents: float
    Telephone: Literal["none", "yes"]
    ForeignWorker: Literal["yes", "no"]


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
