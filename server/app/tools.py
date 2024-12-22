import os
import sys
from typing import Any, Callable, List

import requests
from app.cust_logger import logger, set_files_message_color
from app.state import AgentState
from app.types import Flow, FlowToolResponse
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import StructuredTool

magneto_api_url = "https://magneto-api-dev.rely.io/api/v1"
token = ""

# Test message: Create GKE cluster

set_files_message_color("YELLOW")

env_var_key = "TAVILY_API_KEY"
model_path: str | None = os.getenv(env_var_key)

if not model_path:
    logger.fatal(f"Fatal Error: The '{env_var_key}' environment variable is missing.")
    sys.exit(1)


def fetch_all_flows_mock() -> dict:
    """Make a sync API request to get All flows."""

    return {
        "data": [
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
    }


def fetch_all_flows() -> dict:
    """Make a sync API request to get All flows."""
    headers: dict[str, str] = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        # TODO: Add pagination
        response: requests.Response = requests.get(
            f"{magneto_api_url}/flows?filters=type:eq:selfServiceAction",
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        json = response.json()
        return json["items"]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching flows: {e}")
        return fetch_all_flows_mock()


def fetch_flow_tool(query: str, state: AgentState) -> FlowToolResponse:
    """Find the flow that matches the query and store it in state."""
    flows = fetch_all_flows_mock()["data"]

    # Break query into meaningful keywords
    keywords = [
        word.strip().lower() for word in query.split() if len(word.strip()) > 2
    ]  # Skip small words
    logger.info(f"Searching with keywords: {keywords}")

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
        state.found_flow = flow

        if len(matches) == 1:
            return FlowToolResponse(
                found=True,
                flow=flow,
                flows=None,
                message=f"I found the flow '{flow['title']}' ({flow['description']}) matching {len(keywords)} keywords. Would you like to execute this flow?",
            )
        else:
            return FlowToolResponse(
                found=True,
                flow=flow,
                flows=[m[0] for m in matches],
                message=f"I found {len(matches)} flows. The best match is '{flow['title']}' ({flow['description']}). Would you like to execute this flow?",
            )

    return FlowToolResponse(
        found=False,
        flow=None,
        flows=flows,
        message=f"I couldn't find any flows matching your keywords: {keywords}. Here are all available flows: {flows}",
    )


def create_flow_run_tool(query: str, state: AgentState) -> FlowToolResponse:
    """Execute the flow stored in state."""
    flow: Flow | None = state.found_flow
    if not flow:
        return FlowToolResponse(
            found=False,
            flow=None,
            flows=None,
            message="No flow was found to execute. Please find a flow first.",
        )

    print(f"Executing flow: {flow}")
    return FlowToolResponse(
        found=True,
        flow=flow,
        flows=None,
        message=f"Flow '{flow['title']}' has been executed successfully.",
    )


# Create structured tools with state
fetch_flow: StructuredTool = StructuredTool.from_function(
    func=fetch_flow_tool,
    name="fetch_flow_tool",
    description="Find a flow/self-service action based on the query and store it for execution.",
)

create_flow_run: StructuredTool = StructuredTool.from_function(
    func=create_flow_run_tool,
    name="create_flow_run_tool",
    description="Execute the previously found flow/self-service action. Must be used after fetch_flow_tool has found a flow.",
)

global_search = TavilySearchResults(
    max_results=2, description="Search the internet for information using Tavily API"
)

TOOLS: List[Callable[..., Any]] = [fetch_flow, create_flow_run, global_search]
