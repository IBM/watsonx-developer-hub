# mcp_server.py
import asyncio
from utils import (
    format_output_to_metadata,
    prepare_api_client,
    prepare_chat_watsonx,
    get_credit_risk_deployment_id,
)

from mcp.server.fastmcp import FastMCP
from typing import Literal

# Create an MCP server
mcp = FastMCP("AutoAI Credit Risk", log_level="ERROR")
api_client = prepare_api_client()
chat_watsonx = prepare_chat_watsonx()


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.tool()
def sub(a: int, b: int) -> int:
    """Subtract two numbers"""
    return a - b


# AutoAI tool
@mcp.tool()
def invoke_credit_risk_deployemnt(person_information: str) -> str:
    """Invoke deployment about credit risk information based on all information about person"""
    from pydantic import BaseModel
    from langchain_core.prompts import PromptTemplate
    from langchain.output_parsers import PydanticOutputParser

    class OutputClass(BaseModel):
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
        EmploymentDuration: Literal[
            "less_1", "1_to_4", "greater_7", "4_to_7", "unemployed"
        ]
        InstallmentPercent: float
        Sex: Literal["female", "male"]
        OthersOnLoan: Literal["none", "co-applicant", "guarantor"]
        CurrentResidenceDuration: float
        OwnsProperty: Literal[
            "savings_insurance", "real_estate", "unknown", "car_other"
        ]
        Age: float
        InstallmentPlans: Literal["none", "stores", "bank"]
        Housing: Literal["own", "free", "rent"]
        ExistingCreditsCount: float
        Job: Literal["skilled", "management_self-employed", "unskilled", "unemployed"]
        Dependents: float
        Telephone: Literal["none", "yes"]
        ForeignWorker: Literal["yes", "no"]

    parser = PydanticOutputParser(pydantic_object=OutputClass)

    prompt = PromptTemplate(
        template="Answer the user query.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | chat_watsonx | parser

    chain_response = chain.invoke({"query": person_information})

    meta_props = format_output_to_metadata(chain_response)

    deployment_id = get_credit_risk_deployment_id()

    return api_client.deployments.score(deployment_id, meta_props)


if __name__ == "__main__":
    asyncio.run(mcp.run_sse_async())
