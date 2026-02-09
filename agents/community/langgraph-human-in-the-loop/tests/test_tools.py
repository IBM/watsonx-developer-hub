"""Tests for custom defined tools in langgraph_hitl.tools."""

from langchain_community.tools import DuckDuckGoSearchResults


def test_import_web_search() -> None:
    from langgraph_hitl.tools import web_search

    assert web_search is not None

    assert callable(web_search)


def test_web_search_type() -> None:
    from langgraph_hitl.tools import web_search

    assert isinstance(web_search, DuckDuckGoSearchResults)
