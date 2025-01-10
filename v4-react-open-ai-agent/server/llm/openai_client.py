import os
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken
from logger.cust_logger import logger, set_files_message_color, format_log_message

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

set_files_message_color("YELLOW")  # Set color for logging in this function


class OpenAIClient:
    def __init__(self, model="gpt-3.5-turbo"):
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.token_limit = 5000

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in the given text using the tiktoken library.
        """
        encoding = tiktoken.encoding_for_model(self.model)
        token_count = len(encoding.encode(text))
        logger.info(format_log_message(f"Token count: {token_count}"))
        return token_count

    def inference(self, messages: list) -> str:
        """
        Send a list of messages to the OpenAI API for conversational context.
        If the messages exceed the token limit, summarize them into one message.
        Each message should be a dictionary with 'role' and 'content' keys.
        """

        # if token_count > self.token_limit:
        #     logger.info(
        #         format_log_message(f"Combined text exceeds token limit. Summarizing...")
        #     )
        #     summarized_text = self._summarize_large_input(combined_text)
        #     logger.info(format_log_message(f"Sumarrized text: {summarized_text}. "))
        #     messages = [{"role": "system", "content": summarized_text}]

        chat_completion = self.client.chat.completions.create(
            messages=messages, model=self.model, temperature=0
        )
        return chat_completion.choices[0].message.content.strip()
