import os
from typing import Any, Callable, List, Optional, TypedDict

import requests
from app.state import AgentState
from app.types import Flow, FlowToolResponse
from langchain_core.tools import StructuredTool

magneto_api_url = "https://magneto-api-dev.rely.io/api/v1"
token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ijl5d0ZIc01qZ1NmSmxjX1ZfcUI0ayJ9.eyJodHRwczovL2Rldi1hcHAucmVseS5pby9lbWFpbCI6InZpa3RvcitkZXZAcmVseS5pbyIsImh0dHBzOi8vZGV2LWFwcC5yZWx5LmlvL3VzZXJfbmFtZSI6IlZpa3RvciBWYXN5bGtvdnNreWkiLCJodHRwczovL2Rldi1hcHAucmVseS5pby9leHRlcm5hbF91c2VyX2lkIjoiMTAwMDU1MSIsImh0dHBzOi8vZGV2LWFwcC5yZWx5LmlvL2V4dGVybmFsX29yZ2FuaXphdGlvbl9pZCI6IjEiLCJodHRwczovL2Rldi1hcHAucmVseS5pby9leHRlcm5hbF9vcmdhbml6YXRpb25fbmFtZSI6IlJlbHkiLCJpc3MiOiJodHRwczovL2Rldi5hdXRoLnJlbHkuaW8vIiwic3ViIjoiYXV0aDB8NjYyZjY2YjkwY2QzZDBmNDY2ZWZjY2ViIiwiYXVkIjpbImh0dHBzOi8vZGV2LXJlbHlpby5ldS5hdXRoMC5jb20vYXBpL3YyLyIsImh0dHBzOi8vZGV2LXJlbHlpby5ldS5hdXRoMC5jb20vdXNlcmluZm8iXSwiaWF0IjoxNzM0NzM5MDUzLCJleHAiOjE3MzQ4MjU0NTMsInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwgb2ZmbGluZV9hY2Nlc3MiLCJhenAiOiJVYTJJRVU0bElxYzZJbDd0d01Dd21rMTlGaHhSaWN6YiJ9.tsCaDyNDT2_gU9Cgg0vKoplWBjXi7mqK2dB5Am37rRjJQij00nnfw4Xm0y_ZnyVRpLE-hVOpfPaNGPFhAOPnCIXxxKFMDkpzNLr2sOZFvDwMmLSH2tmvKIQkMQC1Rf6PdY1NIQ13Hm5woczYz-H3WW5MzTBJENXCt1bRLyDmFx_oCBMhTxTY0emXKmJ34kgs6v4gwb9T1RoauQkjlAdKRYeTtReeIstvRvEHyohTnHDFsKe7Oa1HMTNmqf8OCY4_6-c8yW_I6DvXQP9l2LsTGPpCqfd1QLWMPwDFOoT1vWRxVQysdnbiViaEAtRgm7I2FcSFWOf5OK0BwIHY2z2R4w"

# Test message: Create GKE cluster


def fetch_all_flows_mock() -> dict:
    """Make a sync API request to get All flows."""
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
    flows = fetch_all_flows()
    query_lower = query.lower().strip()

    for flow in flows:
        # Get non-empty flow attributes
        flow_id = flow.get("id", "").lower().strip()
        flow_title = flow.get("title", "").lower().strip()
        flow_desc = flow.get("description", "").lower().strip()

        # Only check non-empty values
        matches = []
        if flow_id and flow_id in query_lower:
            matches.append(("id", flow_id))
        if flow_title and flow_title in query_lower:
            matches.append(("title", flow_title))
        if flow_desc and flow_desc in query_lower:
            matches.append(("description", flow_desc))

        if matches:  # If we found any matches
            state.found_flow = flow
            print(f"Found flow: {flow}")
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
