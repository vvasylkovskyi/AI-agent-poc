import os
import sys
from typing import Any, Callable, List

from logger.cust_logger import logger, set_files_message_color
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults

from langchain.tools.retriever import create_retriever_tool
from rag_index.rag_index import RagIndex

load_dotenv()

set_files_message_color("YELLOW")

env_var_key = "TAVILY_API_KEY"
model_path: str | None = os.getenv(env_var_key)

if not model_path:
    logger.fatal(f"Fatal Error: The '{env_var_key}' environment variable is missing.")
    sys.exit(1)


class Tools:
    def __init__(self):
        pass

    def get_tools(self):
        global_search = TavilySearchResults(
            max_results=2,
            description="Search the internet for information using Tavily API",
        )

        retriever_tool = create_retriever_tool(
            RagIndex().retriever,
            "retrieve_blog_posts",
            "Search and return information about Lilian Weng blog posts on LLM agents, prompt engineering, and adversarial attacks on LLMs.",
        )

        TOOLS: List[Callable[..., Any]] = [global_search, retriever_tool]
        return TOOLS
