import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults

web_search = DuckDuckGoSearchResults(output_format="list")


@tool(parse_docstring=True)
def get_arxiv_contents(url: str) -> str:
    """
    Retrieves the content of an arXiv research paper

    Args:
        url: The URL to an arXiv research paper, must be in format 'https://arxiv.org/html/2501.12948v1'

    Returns:
        Full contents of an arXiv research paper
    """
    if "arxiv.org/html/" not in url:
        return "URL must be in format https://arxiv.org/html/<paper_id>"

    html = httpx.get(url).text
    soup = BeautifulSoup(html, "lxml")

    article = soup.find("article")
    if not article:
        return "Could not find paper content"

    for tag in article(["script", "style", "nav", "table", "figure", "img", "math"]):
        tag.decompose()

    return article.get_text(" ", strip=True)
