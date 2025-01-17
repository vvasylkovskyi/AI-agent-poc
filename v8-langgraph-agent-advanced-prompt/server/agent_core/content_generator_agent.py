import os
import sys
import json

from logger.cust_logger import logger, set_files_message_color, format_log_message

from dotenv import load_dotenv
from langchain_core.runnables.config import RunnableConfig
from langchain_google_vertexai import ChatVertexAI
from langchain_openai import ChatOpenAI
from agent_core.prompts.system_prompts import CONTENT_GENERATOR_PROMPT
from agent_core.prompts.prompt_by_key import PROMPTS_BY_KEY
from langchain_core.messages import BaseMessage
from typing import Dict, Any
from agent_core.prompts.linear_ticket_prompt import parser as linear_ticket_parser

set_files_message_color("GREEN")  # Set color for logging in this function

load_dotenv()
env_var_key = "OPENAI_API_KEY"
model_path: str | None = os.getenv(env_var_key)

# If the API key is missing, log a fatal error and exit the application, no need to run LLM application without model!
if not model_path:
    logger.fatal(f"Fatal Error: The '{env_var_key}' environment variable is missing.")
    sys.exit(1)


# https://python.langchain.com/docs/integrations/memory/postgres_chat_message_history/
#
class ContentGeneratorAgent:
    def __init__(self):

        # https://python.langchain.com/docs/integrations/chat/google_vertex_ai_palm/
        self.model = ChatVertexAI(
            model="gemini-1.5-pro",
            temperature=0,
        )

        # self.model = ChatOpenAI(
        #     model="gpt-3.5-turbo",
        #     temperature=0,
        # )

    def _get_messages_with_system_prompt(self, messages):
        return [CONTENT_GENERATOR_PROMPT] + messages

    def _get_prompt_by_key(self, key: str):
        return PROMPTS_BY_KEY[key]

    async def invoke_with_template(
        self, prompt_key: str, template_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke the model using a template prompt with provided arguments.

        Args:
            prompt_key: Key to lookup the prompt template
            template_args: Dictionary of arguments to format the prompt template

        Returns:
            Dict containing the structured response from the model
        """
        logger.info(
            format_log_message(
                f"invoke_with_template: invoking model with template {prompt_key}"
            )
        )
        prompts = self._get_prompt_by_key(prompt_key)

        # Format the template prompt with provided arguments
        formatted_prompts = []
        for prompt in prompts:
            if hasattr(prompt, "format"):  # PromptTemplate
                formatted_prompts.append(prompt.format(**template_args))
            else:  # SystemMessage
                formatted_prompts.append(prompt)

        response: BaseMessage = self.model.invoke(formatted_prompts)

        # Parse the response using the appropriate parser
        if prompt_key == "linear_ticket":
            parsed_response = linear_ticket_parser.parse(response.content)
            return parsed_response.dict()
        else:
            return {"content": response.content}

    async def invoke(self, input_message: str, language: str, config: RunnableConfig):
        logger.info(format_log_message(f"call_model: invoking model"))
        messages = self._get_messages_with_system_prompt([input_message])
        response: BaseMessage = self.model.invoke(messages)
        return response.content
