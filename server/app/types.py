from typing import List, Optional, TypedDict


class Flow(TypedDict):
    id: str
    title: str
    description: str


class FlowToolResponse(TypedDict):
    found: bool
    flow: Optional[Flow]
    flows: Optional[List[Flow]]
    message: str
