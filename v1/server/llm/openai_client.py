import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

class OpenAIClient:
    def __init__(self, model="gpt-3.5-turbo"):
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def inference(self, messages: list) -> str:
        """
        Send a list of messages to the OpenAI API for conversational context.
        Each message should be a dictionary with 'role' and 'content' keys.
        """
        chat_completion = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            temperature=0
        )
        return chat_completion.choices[0].message.content.strip()