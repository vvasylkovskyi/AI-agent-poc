import json
from datetime import datetime
import inspect

from llm.openai_client import OpenAIClient
from tools.tool import Tool, ToolChoice
from logger.cust_logger import logger, set_files_message_color, format_log_message
from pydantic import BaseModel
from enum import Enum
from agent_core.utils import model_structure_repr, extract_first_nested_dict

set_files_message_color("GREEN")  # Set color for logging in this function


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ReactEnd(BaseModel):
    stop: bool
    final_answer: str


class ReActAgent:
    def __init__(self):
        self.system_prompt = """You are an assistant that knows how to use tools. You are an intelligent assistant capable of choosing tools to answer questions.
                            For each query, evaluate the available tools based on their names and descriptions and choose the most suitable one.
                            Explain why the chosen tool is appropriate. Answer user questions clearly and concisely."""
        self.client = OpenAIClient()
        self.history = []
        self.reasoning = []

        self.tools = []
        self.request = []
        self.token_count = 0
        self.token_limit = 5000

    def get_history(self):
        return [{"role": "system", "content": self.system_prompt}] + self.history

    def append_reasoning(self, reasoning):
        self.reasoning.append(reasoning)

    def append_message(self, message):
        self.history.append(message)

        # combined_text = "\n".join([msg["content"] for msg in self.history])
        # self.token_count = self.client.count_tokens(combined_text)

        # # Check if token_count exceeds the limit
        # if self.token_count > self.token_limit and len(self.history) > 1:
        #     # Keep the system message (first one)
        #     system_message = self.history[0]

        #     # Remove older messages but keep recent context
        #     # Keep last 3 messages for context plus the system message
        #     recent_messages = self.history[-3:]

        #     # Reassign history with system message and recent messages
        #     self.history = [system_message] + recent_messages

        #     # Recalculate token count
        #     combined_text = "\n".join([msg["content"] for msg in self.history])
        #     self.token_count = self.client.count_tokens(combined_text)

        #     logger.info(
        #         format_log_message(
        #             f"History truncated. New token count: {self.token_count}"
        #         )
        #     )

    def background_info(self) -> str:
        return (
            f"Here are your previous think steps: {self.reasoning[1:]}"
            if len(self.reasoning) > 1
            else ""
        )

    def can_answer(self, should_answer_directly: bool = False) -> str:
        check_final_str = self.client.inference(
            [
                {
                    "role": "system",
                    "content": f"Is {self.background_info()} enough to finally answer to this request: {self.request}. "
                    f"Respond in a JSON format that contains the following keys: {model_structure_repr(ReactEnd)}",
                }
            ],
        )

        check_final = json.loads(check_final_str)
        observation_step = f"Observation: {check_final['final_answer']}."
        logger.info(format_log_message(observation_step))
        self.append_reasoning(observation_step)

        if check_final["stop"] and should_answer_directly:
            self.append_message(
                {"role": MessageRole.ASSISTANT, "content": check_final["final_answer"]}
            )
        return check_final["stop"]

    def answer(self):
        observation_step = f"Observation: I now know the final answer."
        logger.info(format_log_message(observation_step))
        self.append_reasoning(observation_step)

        prompt = f"""Give the final answer the following request: {self.request}.
                given {self.background_info()}
                """

        final_answer = self.client.inference(
            [{"role": "system", "content": prompt}] + self.get_history()
        )

        logger.info(format_log_message(f"Observation: Final Answer:{final_answer}."))
        self.append_message({"role": MessageRole.ASSISTANT, "content": final_answer})

    def observation(self) -> None:
        observation_step = f"Observation: {self.reasoning[-1]}."
        self.append_reasoning(observation_step)

        check_if_can_answer = self.can_answer()
        if check_if_can_answer:
            self.answer()
        else:
            logger.info(
                format_log_message("Observation: No final answer yet. Thinking again")
            )
            self.think()

    def action(self, tool: Tool) -> None:
        parameters = inspect.signature(tool.func).parameters

        # Create field definitions for Pydantic model
        field_definitions = {}
        for name, param in parameters.items():
            # Get the annotation, default to str if not specified
            annotation = (
                param.annotation if param.annotation != inspect.Parameter.empty else str
            )
            # Setting default value if it exists, else None
            default_value = (
                param.default if param.default != inspect.Parameter.empty else None
            )
            field_definitions[name] = (annotation, default_value)

        # Create the dynamic class with proper annotations
        class DynamicClass(BaseModel):
            pass

        # Set the class annotations first
        DynamicClass.__annotations__ = {
            name: annotation for name, (annotation, _) in field_definitions.items()
        }

        # Then set any default values
        for name, (_, default) in field_definitions.items():
            if default is not None:
                setattr(DynamicClass, name, default)

        output_format = DynamicClass
        prompt = f"""To Answer the following request as best you can: {self.request}.
            {self.background_info()}
            Determine the inputs to send to the tool: {tool.name}
            Given that the source code of the tool function is: {inspect.getsource(tool.func)}.
            Respond in a JSON format that contains the following keys: {model_structure_repr(output_format)}
            """

        response = self.client.inference(
            [{"role": MessageRole.SYSTEM, "content": prompt}] + self.history
        )
        action_step = f"Action: {response}"
        logger.info(format_log_message(action_step))
        self.append_reasoning(action_step)

        input_parameters = extract_first_nested_dict(json.loads(response))
        try:
            action_result = tool.func(**input_parameters)
        except Exception as e:
            action_result = str(e)
            return self.think()
        action_result_step = f"Results of action: {action_result}"
        self.append_reasoning(action_result_step)
        logger.info(format_log_message(action_result_step))
        self.observation()

    def choose_action(self) -> None:
        output_format = ToolChoice
        no_tool_response = json.dumps(
            {
                "tool_name": "none",
                "reason_of_choice": "No tool needed for this response",
            }
        )

        prompt = f"""To Answer the following request as best you can: {self.request}.
            {self.background_info()}
            Choose the tool to use if need be. The tool should be among:
            {[tool.name for tool in self.tools]}.
            If no tool is needed to answer the question, respond with {no_tool_response}
            If you used history to answer the question, respond with {no_tool_response}
            Respond in a JSON format that contains the following keys: {model_structure_repr(output_format)}
            """

        response = self.client.inference(
            [{"role": MessageRole.SYSTEM, "content": prompt}]
        )

        json_reponse = json.loads(response)
        choose_action_step = f"Choose Action: I should use this tool: {json_reponse['tool_name']}. {json_reponse['reason_of_choice']}"
        self.append_reasoning(choose_action_step)
        logger.info(format_log_message(choose_action_step))

        if json_reponse["tool_name"].lower() == "none":
            # If no tool is needed, just respond directly
            response = self.client.inference(self.get_history())
            self.append_message({"role": MessageRole.ASSISTANT, "content": response})
            logger.info(format_log_message(f"Direct Response: {response}"))
            return

        # If a tool is needed, proceed with tool execution
        tool = [
            tool for tool in self.tools if tool.name == json_reponse["tool_name"]
        ].pop()

        self.action(tool)

    def think(self):
        prompt = f"""Answer the following request as best you can: {self.request}.
            {self.background_info()}
            First think about what to do. What action to take first if any.
            Here are the tools at your disposal: {[tool.name for tool in self.tools]}. 
            If there is no tool to use, respond with "I don't know how to answer this question"""

        response = self.client.inference(
            [{"role": MessageRole.SYSTEM, "content": prompt}] + self.history
        )

        thinking_step = f"Think: {response}"
        self.append_reasoning(thinking_step)
        logger.info(format_log_message(thinking_step))

        self.choose_action()

    def react(self, question: str) -> str:
        self.request = question
        self.append_message({"role": MessageRole.USER, "content": question})
        self.reasoning = []

        try_answer_directly = self.can_answer(should_answer_directly=True)
        if try_answer_directly:
            logger.info(format_log_message("React: Can answer directly"))
            return self.history[-1]["content"]

        logger.info(format_log_message("React Start thinking..."))
        self.think()
        self.reasoning = []

        return self.history[-1]["content"]

    def add_tool(self, tool: Tool) -> None:
        self.tools.append(tool)
