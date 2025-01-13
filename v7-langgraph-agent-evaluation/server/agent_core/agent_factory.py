from agent_core.react_agent import ReActAgent
from enum import Enum


class AgentType(str, Enum):
    ReActAgent = "ReActAgent"


class AgentFactory:
    def __init__(self):
        pass

    def create_agent(self, agent_type):
        if agent_type == AgentType.ReActAgent:
            return ReActAgent()
