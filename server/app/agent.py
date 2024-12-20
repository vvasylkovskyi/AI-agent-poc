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
        # Define the two nodes we will cycle between
        builder.add_node("call_model", self.call_model)
        builder.add_node("human_approval", self.wait_for_human_approval)
        builder.add_node("tools", ToolNode(self.tools))

        # Set the entrypoint as `call_model`
        builder.add_edge(START, "call_model")
        builder.add_conditional_edges(
            "call_model",
            self.route_model_output,
        )
        builder.add_conditional_edges(
            "human_approval",
            self.route_human_approval,
        )
        builder.add_edge("tools", "call_model")

        # Compile with checkpointer
        self.agent: CompiledStateGraph = builder.compile(checkpointer=self.memory)

    def route_model_output(
        self, state: AgentState
    ) -> Literal["__end__", "human_approval", "tools"]:
        """Determine the next node based on the model's output.

        Args:
            state (State): The current state of the conversation.

        Returns:
            str: The name of the next node to call ("__end__", "human_approval", or "tools").
        """
        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage):
            raise ValueError(
                f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
            )
        # If there is no tool call, then we finish
        if not last_message.tool_calls:
            return END

        # Check if the create tool is called
        print(last_message.tool_calls)
        for call in last_message.tool_calls:
            if call["name"] == "create_flow_run_tool":
                return "human_approval"

        # Otherwise proceed to execute the requested tools
        return "tools"

    def route_human_approval(self, state: AgentState) -> Literal["tools", "__end__"]:
        """Route based on human approval for the create tool."""
        human_approved = state.get("human_approval", False)
        if human_approved:
            return "tools"
        return END

    def wait_for_human_approval(self, state: AgentState) -> Dict[str, str]:
        """Wait for human approval to execute the create tool.

        Simulates a mechanism to collect approval (e.g., a UI or a prompt).
        """
        # In a real-world implementation, this would be a UI request or a blocking event
        print("Human approval required to execute 'create' tool.")
        approval: bool = input("Approve execution? (yes/no): ").strip().lower() == "yes"
        return {"human_approval": approval}

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
