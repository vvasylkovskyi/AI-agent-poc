from typing import Any, Callable, List, Optional, TypedDict

from app.state import AgentState
from app.types import Flow, FlowToolResponse
from langchain_core.tools import StructuredTool


def fetch_all_flows() -> dict:
    """Make a sync API request to get All flows."""
    token = "my_token"
    headers: dict[str, str] = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

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


def fetch_flow_tool(query: str, state: AgentState) -> FlowToolResponse:
    """Find the flow that matches the query and store it in state."""
    flows = fetch_all_flows()["data"]

    for flow in flows:
        if (
            flow["id"].lower() in query.lower()
            or flow["title"].lower() in query.lower()
            or flow["description"].lower() in query.lower()
        ):
            # Store the found flow in state for the next tool
            state.found_flow = flow
            return FlowToolResponse(
                found=True,
                flow=flow,
                flows=None,
                message=f"I found the flow '{flow['title']}' ({flow['description']}). Would you like to execute this flow?",
            )

    # If no specific flow found, return all flows
    return FlowToolResponse(
        found=False,
        flow=None,
        flows=flows,
        message=f"Here are the available flows: {flows}. Which one would you like to use?",
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
    description="Find a flow based on the query and store it for execution.",
)

create_flow_run: StructuredTool = StructuredTool.from_function(
    func=create_flow_run_tool,
    name="create_flow_run_tool",
    description="Execute the previously found flow. Must be used after fetch_flow_tool has found a flow.",
)

TOOLS: List[Callable[..., Any]] = [fetch_flow, create_flow_run]
