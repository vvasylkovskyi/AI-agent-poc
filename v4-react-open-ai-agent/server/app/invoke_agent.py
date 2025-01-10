import json
from datetime import datetime

from logger.cust_logger import logger, set_files_message_color, format_log_message
from fastapi import WebSocket
from agent_core.agent import ReActAgent
from tools.tool import Tool
from tools.calculation import perform_calculation
from tools.date import date_of_today
from tools.search_wikipedia import search_wikipedia

set_files_message_color("MAGENTA")  # Set color for logging in this function

# Store agents for each session
# TODO - store the sessions in the database to ensure stateless architecture on the server

active_sessions = {}


async def invoke_agent(websocket: WebSocket, data: str, user_uuid: str):
    agent = {}

    if user_uuid in active_sessions:
        agent = active_sessions[user_uuid]
    else:
        agent = ReActAgent()
        # Creating instances of the Tool class
        wikipedia_search_tool = Tool(
            "WikipediaSearch",
            "Too for searching Wikipedia. Use it when you need to find information on the internet to answer user questions",
            search_wikipedia,
        )
        calculator_tool = Tool(
            "Calculator",
            "Tool for performing calculations, use it when you need to calculate something",
            perform_calculation,
        )
        date_request_tool = Tool(
            "Date_of_request",
            "Tool for returning the current date. Use when the you need to answer something related to the current date",
            date_of_today,
        )
        agent.add_tool(wikipedia_search_tool)
        agent.add_tool(calculator_tool)
        agent.add_tool(date_request_tool)
        active_sessions[user_uuid] = agent

    answer = agent.react(data)
    logger.info(format_log_message(f"Assistant: {answer}"))
    answer_str = json.dumps({"on_chat_model_stream": answer})
    await websocket.send_text(answer_str)
