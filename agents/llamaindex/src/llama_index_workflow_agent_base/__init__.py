from llama_index.core.tools import FunctionTool
from .tools import dummy_web_search

TOOLS = [FunctionTool.from_defaults(dummy_web_search)]
