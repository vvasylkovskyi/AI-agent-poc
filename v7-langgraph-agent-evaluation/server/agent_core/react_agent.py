import os
import sys

from logger.cust_logger import logger, set_files_message_color

from agent_core.tools import Tools
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_google_vertexai import ChatVertexAI
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph

from logger.cust_logger import logger, set_files_message_color, format_log_message
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

set_files_message_color("GREEN")  # Set color for logging in this function

load_dotenv()
env_var_key = "OPENAI_API_KEY"
model_path: str | None = os.getenv(env_var_key)

# If the API key is missing, log a fatal error and exit the application, no need to run LLM application without model!
if not model_path:
    logger.fatal(f"Fatal Error: The '{env_var_key}' environment variable is missing.")
    sys.exit(1)


class ReActAgent:
    def __init__(self):

        # https://python.langchain.com/docs/integrations/chat/google_vertex_ai_palm/
        # self.model = ChatVertexAI(
        #     model="gemini-1.5-pro",
        #     temperature=0,
        # )

        self.model = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
        )
        self.memory = MemorySaver()

        self.agent_graph_runnable: CompiledStateGraph = create_react_agent(
            self.model, tools=Tools().get_tools(), checkpointer=self.memory
        )

    async def invoke(self, input_message: str, language: str, config: RunnableConfig):
        state = await self.agent_graph_runnable.ainvoke(
            {"messages": input_message, "language": language}, config
        )
        return state["messages"][-1].content
