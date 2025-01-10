import os
import sys
from typing import Dict, Literal

from app.cust_logger import logger, set_files_message_color
from app.prompts import SYSTEM_PROMPT
from app.state import AgentState
from app.tools import TOOLS
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_google_vertexai import ChatVertexAI
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from k8s_agent.agent import agent_chain
set_files_message_color("MAGENTA")  # Set color for logging in this function

load_dotenv()
env_var_key = "OPENAI_API_KEY"
model_path: str | None = os.getenv(env_var_key)

# If the API key is missing, log a fatal error and exit the application, no need to run LLM application without model!
if not model_path:
    logger.fatal(f"Fatal Error: The '{env_var_key}' environment variable is missing.")
    sys.exit(1)

# Initialize the ChatModel LLM
# ChatModel vs LLM concept https://python.langchain.com/docs/concepts/#chat-models
# Available ChatModel integrations with LangChain https://python.langchain.com/docs/integrations/chat/
model = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
)

# https://python.langchain.com/docs/integrations/chat/google_vertex_ai_palm/
# model = ChatVertexAI(
#     model="gemini-1.5-pro",
#     temperature=0,
# )
model_with_tools = model.bind_tools(TOOLS)


def get_messages_with_prompt(messages):
    return [SYSTEM_PROMPT] + messages


# Define the node that calls the model
# def call_model(state: AgentState, config: RunnableConfig):
#     # Configure the model with tools
#     messages = get_messages_with_prompt(state.messages)  # Convert Sequence to list
#     response: BaseMessage = model_with_tools.invoke(messages)
#     # response: BaseMessage = model.invoke(messages)
#     return {"messages": [response]}

def call_model(state: AgentState, config: RunnableConfig):
    # Configure the model with tools
    # messages = get_messages_with_prompt(state.messages)  # Convert Sequence to list
    response: BaseMessage = agent_chain.run(state.messages[-1])
    # response: BaseMessage = model.invoke(messages)
    return {"messages": [response]}


def route_model_output(state: AgentState) -> Literal["__end__", "tools"]:
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
        return "__end__"
    return "tools"


graph = StateGraph(state_schema=MessagesState)
graph.add_node("call_model", call_model)
graph.add_node("tools", ToolNode(TOOLS))

# Set the entrypoint as call_model
graph.add_edge(START, "call_model")
graph.add_conditional_edges(
    "call_model",
    route_model_output,
)

graph.add_edge("call_model", END)
graph.add_edge("tools", "call_model")

memory = MemorySaver()  # Checkpointing mechanism to save conversation by thread_id
# https://langchain-ai.github.io/langgraph/how-tos/persistence/

graph_runnable: CompiledStateGraph = graph.compile(checkpointer=memory)
