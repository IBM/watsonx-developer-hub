from beeai_framework.tools import StringToolOutput, tool


@tool
def dummy_web_search(query: str) -> StringToolOutput:
    """
    Web search tool that return static list of strings.

    Args:
        query: User query to search in web.

    Returns:
        Dummy list of web search results.
    """
    return StringToolOutput("IBM watsonx.ai")
