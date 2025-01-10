import os
import sys
from typing import Literal

from logger.cust_logger import logger, set_files_message_color
from agent_core.prompts import SYSTEM_PROMPT
from agent_core.state import AgentState
from agent_core.tools import Tools
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_google_vertexai import ChatVertexAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from logger.cust_logger import logger, set_files_message_color, format_log_message

set_files_message_color("GREEN")  # Set color for logging in this function

load_dotenv()
env_var_key = "OPENAI_API_KEY"
model_path: str | None = os.getenv(env_var_key)

# If the API key is missing, log a fatal error and exit the application, no need to run LLM application without model!
if not model_path:
    logger.fatal(f"Fatal Error: The '{env_var_key}' environment variable is missing.")
    sys.exit(1)


###
# Note, we may want to improve this agent to be more reAct like
# Here is example of prebuild agent - https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/prebuilt/chat_agent_executor.py
# See def create_react_agent
###
class LangGraphAgent:
    def __init__(self):

        # https://python.langchain.com/docs/integrations/chat/google_vertex_ai_palm/
        self.model = ChatVertexAI(
            model="gemini-1.5-pro",
            temperature=0,
        )

        tools = Tools().get_tools()

        self.model_with_tools = self.model.bind_tools(tools)
        self.graph = StateGraph(state_schema=AgentState)
        self.graph.add_node("call_model", self._call_model)
        self.graph.add_node("tools", ToolNode(tools))

        # Set the entrypoint as call_model
        self.graph.add_edge(START, "call_model")
        self.graph.add_conditional_edges(
            "call_model",
            self._route_model_output,
        )

        self.graph.add_edge("call_model", END)
        self.graph.add_edge("tools", "call_model")

        # Checkpointing mechanism to save conversation by thread_id
        # https://langchain-ai.github.io/langgraph/how-tos/persistence/
        memory = MemorySaver()

        self.agent_graph_runnable: CompiledStateGraph = self.graph.compile(
            checkpointer=memory
        )

    def _get_messages_with_prompt(self, messages):
        return [SYSTEM_PROMPT] + messages

    # Define the node that calls the model
    def _call_model(self, state: AgentState):
        logger.info(format_log_message(f"call_model: invoking model"))
        messages = self._get_messages_with_prompt(state.messages)
        response: BaseMessage = self.model_with_tools.invoke(messages)
        return {"messages": [response]}

    def _route_model_output(self, state: AgentState) -> Literal["__end__", "tools"]:
        """Determine the next node based on the model's output.

        This function checks if the model's last message contains tool calls.

        Args:
            state (State): The current state of the conversation.

        Returns:
            str: The name of the next node to call ("__end__" or "tools").
        """
        last_message = state.messages[-1]
        if not isinstance(last_message, AIMessage):
            raise ValueError(f"Expected AIMessage, got {type(last_message).__name__}")

        if not last_message.tool_calls:
            logger.info(format_log_message(f"route_model_output: ending graph"))
            return "__end__"

        logger.info(format_log_message(f"route_model_output: returning tools"))
        return "tools"

    def invoke(self, message: str, language: str, config: RunnableConfig):
        input_messages = [HumanMessage(message)]
        state = self.agent_graph_runnable.invoke(
            {"messages": input_messages, "language": language}, config
        )
        return state["messages"][-1].content
