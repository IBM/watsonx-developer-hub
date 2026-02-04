import pytest
import httpx
from langgraph_react_agent.tools import get_arxiv_contents


class MockResponse:
    def __init__(self, text):
        self.text = text


@pytest.mark.parametrize(
    "url, mock_html, expected_output",
    [
        (
            "https://arxiv.org/html/2501.12948v1",
            "<html><body><article><p>Transformed content from the HTML</p></article></body></html>",
            "Transformed content from the HTML",
        ),
        (
            "https://arxiv.org/html/2501.12948v1",
            "<html><body>No article here</body></html>",
            "Could not find paper content",
        ),
        (
            "https://arxiv.org/other/1234",
            "",
            "URL must be in format https://arxiv.org/html/<paper_id>",
        ),
    ],
)
class TestTools:
    def test_get_arxiv_contents(self, monkeypatch, url, mock_html, expected_output):
        def mock_get(_url):
            return MockResponse(mock_html)

        monkeypatch.setattr(httpx, "get", mock_get)

        result = get_arxiv_contents(url)
        assert result == expected_output
