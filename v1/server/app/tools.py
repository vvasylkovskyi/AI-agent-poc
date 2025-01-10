import os
import sys
from typing import Any, Callable, List

import requests
from app.cust_logger import logger, set_files_message_color
from app.state import AgentState
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool

# magneto_api_url = "https://magneto-api-dev.rely.io/api/v1"
magneto_api_url = "https://magneto.rely.io/api/v1"
token = ""
# Test message: Create GKE cluster

load_dotenv()

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
        print(f"Error fetching self service actions: {e}")
        return fetch_all_flows_mock()


@tool
def fetch_flow_tool(query: str):
    """Find the self service action that matches the query and return the link to it it."""
    all_flows = fetch_all_flows()
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


global_search = TavilySearchResults(
    max_results=2, description="Search the internet for information using Tavily API"
)

TOOLS: List[Callable[..., Any]] = [fetch_flow_tool, global_search]
