# mcp_server.py
import asyncio
from utils import (
    format_output_to_metadata,
    prepare_api_client,
    get_credit_risk_deployment_id,
    PersonInformation,
)

from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("AutoAI Credit Risk", log_level="ERROR")
api_client = prepare_api_client()


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
def invoke_credit_risk_deployemnt(person_information: PersonInformation) -> dict:
    """Invoke deployment about credit risk information based on all information about person.

    Fill person_information only about possible inputs provided in PersonInformation typing.
    """

    meta_props = format_output_to_metadata(person_information)

    deployment_id = get_credit_risk_deployment_id()

    return api_client.deployments.score(deployment_id, meta_props)


if __name__ == "__main__":
    asyncio.run(mcp.run_sse_async())
