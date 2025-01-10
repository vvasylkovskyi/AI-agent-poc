from agent_core.lang_graph_agent import LangGraphAgent
from enum import Enum


class AgentType(str, Enum):
    LangGraph = "LangGraph"


class AgentFactory:
    # def __init__(self):

    def create_agent(self, agent_type):
        if agent_type == AgentType.LangGraph:
            return LangGraphAgent()
