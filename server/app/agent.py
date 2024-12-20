import getpass
import os
from typing import Dict, List, Literal, cast

from app.prompts import SYSTEM_PROMPT
from app.state import AgentState
from app.tools import TOOLS
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import StateSnapshot


class Agent:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        if not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

        if not os.environ.get("TAVILY_API_KEY"):
            os.environ["TAVILY_API_KEY"] = getpass.getpass("Enter API key for Tavily: ")

        self.tools = TOOLS

        self.model = ChatOpenAI(model="gpt-3.5-turbo")
        # self.model_with_tools = load_chat_model("gpt-3.5-turbo").bind_tools(self.tools)
        self.model_with_tools = self.model.bind_tools(self.tools)
        # Add memory
        self.memory = MemorySaver()

        builder = StateGraph(state_schema=MessagesState)
        # Define the two nodes we will cycle between
        builder.add_node("call_model", self.call_model)
        builder.add_node("tools", ToolNode(self.tools))

        # Set the entrypoint as call_model
        builder.add_edge(START, "call_model")
        builder.add_conditional_edges(
            "call_model",
            self.route_model_output,
        )

        builder.add_edge("tools", "call_model")

        # Compile with checkpointer
        self.agent: CompiledStateGraph = builder.compile(checkpointer=self.memory)

    def route_model_output(self, state: AgentState) -> Literal["__end__", "tools"]:
        """Determine the next node based on the model's output.

        This function checks if the model's last message contains tool calls.

        Args:
            state (State): The current state of the conversation.

        Returns:
            str: The name of the next node to call ("__end__" or "tools").
        """
        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage):
            raise ValueError(
                f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
            )
        # If there is no tool call, then we finish
        if not last_message.tool_calls:
            return END
        # Otherwise we execute the requested actions
        return "tools"

    # Define the node that calls the model
    def call_model(self, state: AgentState) -> Dict[str, BaseMessage]:

        # Configure the model with tools
        response: BaseMessage = self.model_with_tools.invoke(
            [SYSTEM_PROMPT] + state["messages"],
        )
        return {"messages": response}

    def chat(self, message: str, language: str, config: RunnableConfig):
        input_messages: List[HumanMessage] = [HumanMessage(message)]
        messages = self.agent.invoke(
            {"messages": input_messages, "language": language}, config
        )
        snapshot: StateSnapshot = self.agent.get_state(config)

        if "tools" in snapshot.next:
            return {"messages": messages["messages"], "waiting_for_tool_response": True}
        return {"messages": messages["messages"], "waiting_for_tool_response": False}
