import getpass
import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START,END, MessagesState, StateGraph
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import (
    Annotated,
    Sequence,
    TypedDict,
)
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """The state of the agent."""

    # add_messages is a reducer
    # See https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers
    messages: Annotated[Sequence[BaseMessage], add_messages]
    

class Agent:
    def __init__(self):
        if not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

        if not os.environ.get("TAVILY_API_KEY"):
            os.environ["TAVILY_API_KEY"] = getpass.getpass("Enter API key for Tavily: ")

        # Define our tools
        search = TavilySearchResults(
            max_results=2,
            description="Search the internet for information using Tavily API"
        )
        self.tools = [search]
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        self.model = ChatOpenAI(model="gpt-3.5-turbo")
        self.model_with_tools = self.model.bind_tools(self.tools)
        # Add memory
        self.memory = MemorySaver()

        workflow = StateGraph(state_schema=MessagesState)
        # Define the two nodes we will cycle between
        workflow.add_node("agent", self.call_model)
        tool_node = ToolNode(tools=[search])
        workflow.add_node("tools", tool_node)

        workflow.add_conditional_edges(
            "agent",
            tools_condition,
        )

        workflow.add_edge(START, "agent")
        workflow.set_entry_point("agent")
        # We now add a normal edge from `tools` to `agent`.
        # This means that after `tools` is called, `agent` node is called next.
        workflow.add_edge("tools", "agent")
        workflow.add_edge("agent", END)

        self.agent = workflow.compile(checkpointer=self.memory,
                                      interrupt_before=["tools"])



    # Define the node that calls the model
    def call_model(self, state: AgentState):
        system_prompt = SystemMessage(
            """You are a helpful AI assistant designed to provide clear, accurate, and useful responses. 
                Your goal is to assist users by:
                - Providing detailed but concise answers
                - Breaking down complex topics into understandable parts
                - Being direct and professional in your communication
                - Admitting when you're not sure about something
                - Using the search tool when you need to find current or factual information
                - Asking for clarification when needed"""
        )
        
        # Configure the model with tools
        response = self.model_with_tools.invoke(
            [system_prompt] + state["messages"],
        )
        return {"messages": response}


    def print_stream_format(self, input_messages, language, config):
        for chunk, metadata in self.agent.stream(
            {"messages": input_messages, "language": language},
            config,
            stream_mode="messages",
        ):
            if isinstance(chunk, AIMessage):  # Filter to just model responses
                print(chunk.content, end="|")        

    def chat(self, message: str, language: str, config: dict):
        input_messages = [HumanMessage(message)]
        messages = self.agent.invoke({"messages": input_messages, "language": language}, config)
        snapshot = self.agent.get_state(config)
        print(snapshot.next)
        if "tools" in snapshot.next:
            return { "messages": messages["messages"], "waiting_for_tool_response": True }
        return { "messages": messages["messages"], "waiting_for_tool_response": False }
    