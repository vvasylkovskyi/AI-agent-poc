import json
from datetime import datetime

from app.cust_logger import logger, set_files_message_color
from fastapi import WebSocket
from k8s_agent.agent import KubernetesAgent

set_files_message_color("MAGENTA")  # Set color for logging in this function

# Store agents for each session
# TODO - store the sessions in the database to ensure stateless architecture on the server

active_sessions = {}

async def invoke_agent(websocket: WebSocket, data: str, user_uuid: str):
    agent = {}

    if user_uuid in active_sessions:
        agent = active_sessions[user_uuid]
    else: 
        agent = KubernetesAgent()
        active_sessions[user_uuid] = agent

    answer = agent.get_answer(data)
    logger.info(
        json.dumps(
            {
                "timestamp": datetime.now().isoformat(),
                "uuid": user_uuid,
                # "llm_method": kind,
                "ai-bot": answer,
            }
        )
    )
    answer_str = json.dumps({ "on_chat_model_stream": answer })
    await websocket.send_text(answer_str)
