import os
import sys
from typing import Any, Callable, List

from logger.cust_logger import logger, set_files_message_color
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool

load_dotenv()

set_files_message_color("YELLOW")

env_var_key = "TAVILY_API_KEY"
model_path: str | None = os.getenv(env_var_key)

if not model_path:
    logger.fatal(f"Fatal Error: The '{env_var_key}' environment variable is missing.")
    sys.exit(1)

global_search = TavilySearchResults(
    max_results=2, description="Search the internet for information using Tavily API"
)

TOOLS: List[Callable[..., Any]] = [global_search]
