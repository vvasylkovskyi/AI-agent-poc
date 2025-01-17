from langchain.prompts import PromptTemplate
from langchain_core.messages import SystemMessage
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List


class LinearTicket(BaseModel):
    title: str = Field(description="The title of the ticket")
    description: str = Field(description="Detailed description of the ticket")


# Create the parser
parser = PydanticOutputParser(pydantic_object=LinearTicket)

LINEAR_TICKET_PROMPT = PromptTemplate(
    template="""You are a Linear ticket creation assistant. Your task is to create well-structured tickets based on the provided information.

Context:
- Project: {project}
- Issue Type: {issue_type}
- Description: {description}

Please create a Linear ticket with the following requirements:
1. Title should be clear, concise, and descriptive
2. Description should include:
   - Detailed explanation of the issue/feature
   - Acceptance criteria (if applicable)
   - Any technical considerations
   - Dependencies (if any)

Current information to process:
{input}

{format_instructions}""",
    input_variables=["project", "issue_type", "description", "input"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

LINEAR_TICKET_SYSTEM_MESSAGE = SystemMessage(
    content="You are a Linear ticket creation assistant that helps create well-structured and detailed tickets. "
    "Focus on clarity, completeness, and actionability in your ticket creation. "
    "Always return your response in the specified format."
)
