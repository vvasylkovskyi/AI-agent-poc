import getpass
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START,END, MessagesState, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

class Agent:
    def __init__(self):
        if not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

        self.model = ChatOpenAI(model="gpt-3.5-turbo")
        # Add memory
        self.memory = MemorySaver()
        workflow = StateGraph(state_schema=MessagesState)
        workflow.add_node("call_model", self.call_model)
        workflow.add_edge(START, "call_model")
        workflow.add_edge("call_model", END)
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                "system",
                """You are a helpful AI assistant designed to provide clear, accurate, and useful responses. 
                Your goal is to assist users by:
                - Providing detailed but concise answers
                - Breaking down complex topics into understandable parts
                - Being direct and professional in your communication
                - Admitting when you're not sure about something
                - Asking for clarification when needed""",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        self.agent = workflow.compile(checkpointer=self.memory)

    # Define the function that calls the model
    def call_model(self,state: MessagesState):
        prompt = self.prompt_template.invoke(state)
        response = self.model.invoke(prompt)
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
        # self.print_stream_format(input_messages, language, config)
        return messages["messages"]
    