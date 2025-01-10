import json

from logger.cust_logger import logger, set_files_message_color, format_log_message
from fastapi import WebSocket
from agent_core.agent_factory import AgentType, AgentFactory

set_files_message_color("MAGENTA")  # Set color for logging in this function

# Store agents for each session
# TODO - store the sessions in the database to ensure stateless architecture on the server
active_sessions = {}


async def invoke_agent(websocket: WebSocket, data: str, user_uuid: str):
    agent = {}

    if user_uuid in active_sessions:
        agent = active_sessions[user_uuid]
    else:
        agent = AgentFactory().create_agent(AgentType.LangGraph)
        active_sessions[user_uuid] = agent

    language = "English"
    config = {"configurable": {"thread_id": str(user_uuid)}}
    answer = agent.invoke(data, language, config)
    logger.info(format_log_message(f"Assistant: {answer}"))
    answer_str = json.dumps({"on_chat_model_stream": answer})
    await websocket.send_text(answer_str)
