import os
import sys
from typing import Any, Callable, List
from pydantic import BaseModel, Field

from logger.cust_logger import logger, set_files_message_color
from dotenv import load_dotenv
from langsmith import traceable
from langchain_core.tools import StructuredTool

load_dotenv()

set_files_message_color("YELLOW")

env_var_key = "TAVILY_API_KEY"
model_path: str | None = os.getenv(env_var_key)

if not model_path:
    logger.fatal(f"Fatal Error: The '{env_var_key}' environment variable is missing.")
    sys.exit(1)


def fetch_all_flows() -> dict:
    """Make a sync API request to get All flows."""

    return [
        {
            "id": "rollout",
            "title": "Rollout app",
            "description": "Rolls out application by defined percentile",
        },
        {
            "id": "order_66",
            "title": "Order 66",
            "description": "Executes order 66 and kills all jedi",
        },
    ]


@traceable(run_type="tool", name="fetch_flow_tool")
def fetch_flow(query: str):
    """Find the self service action that matches the query and return the link to it it."""
    all_flows = fetch_all_flows()

    logger.info(f"User Query: {query}")
    # Map to a list of objects with only 'id', 'title', and 'description'
    flows = [
        {"id": flow["id"], "title": flow["title"], "description": flow["description"]}
        for flow in all_flows
    ]

    # Break query into meaningful keywords
    keywords = [
        word.strip().lower() for word in query.split() if len(word.strip()) > 2
    ]  # Skip small words
    logger.info(f"Searching with keywords: {keywords}")

    if "list" in keywords or "all" in keywords:
        return f"Here are all available self-service actions: {flows}"

    matches = []
    for flow in flows:
        score = 0
        matched_keywords = set()
        # Search through all flow fields
        for field in ["id", "title", "description"]:
            field_value = flow.get(field, "").lower()
            if not field_value:
                continue

            # Check each keyword against this field
            for keyword in keywords:
                if keyword in field_value and keyword not in matched_keywords:
                    score += 1
                    matched_keywords.add(keyword)
        if score > 0:
            matches.append((flow, score, matched_keywords))

    # Sort matches by score
    matches.sort(key=lambda x: x[1], reverse=True)
    logger.info(f"Matches: {matches}")

    if matches:
        best_match = matches[0]
        flow, score, keywords = best_match

        if len(matches) == 1:
            return f"I found the Link to Self Service Action: '{flow['title']}' Here it goes. https://demo.rely.io/self-service/action-details/{flow['id']}/action-details. You can run the self service action from web UI"
        else:
            return f"I found {len(matches)} self service actions. The best match is '{flow['title']}' ({flow['description']})."

    return f"I couldn't find any self service actions matching your keywords: {keywords}. Here are all available self service actions: {flows}"


# Input class for tool so that it can follow strict input parameter schema
class FetchFlowToolInput(BaseModel):
    query: str = Field(..., description="original search query")


fetch_flow_tool = StructuredTool.from_function(
    func=fetch_flow,
    name="fetch_flow",
    description="Use this tool when you want to run self service actions",
    args_schema=FetchFlowToolInput,
)


class Tools:
    def __init__(self):
        pass

    def get_tools(self):

        TOOLS: List[Callable[..., Any]] = [
            fetch_flow_tool,
        ]
        return TOOLS
