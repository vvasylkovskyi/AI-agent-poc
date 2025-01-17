from typing import Dict, List
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage

from .linear_ticket_prompt import LINEAR_TICKET_PROMPT, LINEAR_TICKET_SYSTEM_MESSAGE

PROMPTS_BY_KEY: Dict[str, List[PromptTemplate | SystemMessage]] = {
    "linear_ticket": [LINEAR_TICKET_PROMPT, LINEAR_TICKET_SYSTEM_MESSAGE]
}
