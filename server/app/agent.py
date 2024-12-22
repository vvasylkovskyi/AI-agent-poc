import json
from datetime import datetime

from app.cust_logger import logger, set_files_message_color
from app.graph import graph_runnable
from fastapi import WebSocket
from langchain_core.runnables.config import RunnableConfig

set_files_message_color("MAGENTA")  # Set color for logging in this function


async def invoke_agent(websocket: WebSocket, data: str, user_uuid: str):
    initial_input: dict[str, str] = {"messages": data}
    thread_config: RunnableConfig = {
        "configurable": {"thread_id": user_uuid}
    }  # Pass users conversation_id to manage chat memory on server side
    final_text = ""  # accumulate final output to log, rather then each token

    # Asynchronous event-based response processing, data designated by event as key
    async for event in graph_runnable.astream_events(
        initial_input, thread_config, version="v2"
    ):
        kind: str = event["event"]
        # print("Event: ", event)
        if kind == "on_chat_model_stream":
            chunk = event["data"].get("chunk")
            if chunk and hasattr(chunk, "content"):
                addition: str = chunk.content
                final_text += addition
                if addition:
                    message = json.dumps({"on_chat_model_stream": addition})
                    await websocket.send_text(message)

        elif kind == "on_chat_model_end":
            # Indicate the end of model generation so FE knows the message is over
            message = json.dumps({"on_chat_model_end": True})
            logger.info(
                json.dumps(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "uuid": user_uuid,
                        "llm_method": kind,
                        "sent": final_text,
                    }
                )
            )
            await websocket.send_text(message)

        elif kind == "on_custom_event":
            # sends across custom event as if its its own event for easy working
            # check out `conditional_check` node
            message: str = json.dumps({event["name"]: event["data"]})
            logger.info(
                json.dumps(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "uuid": user_uuid,
                        "llm_method": kind,
                        "sent": message,
                    }
                )
            )
            await websocket.send_text(message)
