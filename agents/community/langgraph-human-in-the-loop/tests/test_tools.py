"""Tests for custom defined tools in langgraph_hitl.tools."""

from langchain_community.tools import DuckDuckGoSearchResults


def test_web_search_type() -> None:
    from langgraph_hitl.tools import web_search

    assert isinstance(web_search, DuckDuckGoSearchResults)
