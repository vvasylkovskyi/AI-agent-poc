from agent_core.react_agent import ReActAgent
from agent_core.content_generator_agent import ContentGeneratorAgent
from enum import Enum


class AgentType(str, Enum):
    ReActAgent = "ReActAgent"
    ContentGeneratorAgent = "ContentGeneratorAgent"


class AgentFactory:
    def __init__(self):
        pass

    def create_agent(self, agent_type):
        if agent_type == AgentType.ReActAgent:
            return ReActAgent()
        if agent_type == AgentType.ContentGeneratorAgent:
            return ContentGeneratorAgent()
