from agent_core.lang_graph_agent import LangGraphAgent
from agent_core.lang_graph_rag_agent import LangGraphRagAgent
from enum import Enum


class AgentType(str, Enum):
    LangGraph = "LangGraph"
    LangGraphRag = "LangGraphRag"


class AgentFactory:
    def __init__(self):
        pass

    def create_agent(self, agent_type):
        if agent_type == AgentType.LangGraph:
            return LangGraphAgent()
        if agent_type == AgentType.LangGraphRag:
            return LangGraphRagAgent()
