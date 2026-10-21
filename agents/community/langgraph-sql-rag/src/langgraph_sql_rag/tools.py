import re
from typing import TYPE_CHECKING

from langchain_core.tools import BaseTool, StructuredTool
from langchain_ibm import ChatWatsonx
from langchain_ibm.agent_toolkits.sql import WatsonxSQLDatabaseToolkit
from langchain_ibm.utilities.sql_database import WatsonxSQLDatabase

if TYPE_CHECKING:
    from ibm_watsonx_ai import APIClient


# Statements are only allowed to start with one of these keywords.
_ALLOWED_FIRST_KEYWORDS = {"SELECT", "WITH", "VALUES"}

# Keywords that must not appear anywhere in a query (outside of string literals,
# quoted identifiers and comments). This also catches data-modifying statements
# nested in a CTE or in a Db2 `FINAL TABLE (INSERT ...)` reference.
_FORBIDDEN_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "UPSERT",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "RENAME",
    "GRANT",
    "REVOKE",
    "CALL",
    "EXEC",
    "EXECUTE",
    "COMMIT",
    "ROLLBACK",
    "LOCK",
    "INTO",
}

_COMMENTS_AND_LITERALS = re.compile(
    r"""
    --[^\n]*            # single-line comment
    | /\*.*?\*/         # multi-line comment
    | '(?:[^']|'')*'    # string literal
    | "(?:[^"]|"")*"    # quoted identifier
    | `[^`]*`           # backtick-quoted identifier
    """,
    re.VERBOSE | re.DOTALL,
)


class ReadOnlyViolationError(ValueError):
    """Raised when a SQL query is not a read-only query."""


def validate_read_only_query(query: str) -> None:
    """Raise `ReadOnlyViolationError` unless `query` is a single read-only statement.

    This is a defense-in-depth check. It does not replace using database
    credentials that only have read privileges.
    """
    stripped = _COMMENTS_AND_LITERALS.sub(" ", query).strip().rstrip(";").strip()

    if not stripped:
        raise ReadOnlyViolationError("Empty SQL query.")

    if ";" in stripped:
        raise ReadOnlyViolationError("Multiple SQL statements are not allowed.")

    words = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", stripped.upper())

    if words[0] not in _ALLOWED_FIRST_KEYWORDS:
        raise ReadOnlyViolationError(
            "Only read-only queries (SELECT / WITH / VALUES) are allowed."
        )

    forbidden = sorted(_FORBIDDEN_KEYWORDS.intersection(words))
    if forbidden:
        raise ReadOnlyViolationError(
            f"Only read-only queries are allowed. Forbidden keyword(s): {', '.join(forbidden)}."
        )


def _read_only_tool(tool: BaseTool) -> BaseTool:
    """Wrap `tool` so that its `query` argument is validated before execution.

    Tools without a `query` argument (e.g. listing tables, getting schema) are
    returned unchanged. Violations are returned to the agent as an error message,
    so it can rewrite its query.
    """
    if "query" not in tool.args or tool.args_schema is None:
        return tool

    def _run(**kwargs):
        try:
            validate_read_only_query(kwargs["query"])
        except ReadOnlyViolationError as e:
            return f"Error: {e}"
        return tool.invoke(kwargs)

    async def _arun(**kwargs):
        try:
            validate_read_only_query(kwargs["query"])
        except ReadOnlyViolationError as e:
            return f"Error: {e}"
        return await tool.ainvoke(kwargs)

    return StructuredTool(
        name=tool.name,
        description=tool.description,
        args_schema=tool.args_schema,
        func=_run,
        coroutine=_arun,
    )


def sql_tools_watsonx(
    api_client: "APIClient",
    tool_config: dict,
) -> list[BaseTool]:
    chat_llm = ChatWatsonx(
        model_id=tool_config["model_id"],
        params={"temperature": 0.2},
        watsonx_client=api_client,
    )

    sql_database = WatsonxSQLDatabase(
        connection_id=tool_config["connection_id"],
        schema=tool_config["schema"],
        watsonx_client=api_client,
    )
    sql_toolkit = WatsonxSQLDatabaseToolkit(db=sql_database, llm=chat_llm)

    return [_read_only_tool(tool) for tool in sql_toolkit.get_tools()]
