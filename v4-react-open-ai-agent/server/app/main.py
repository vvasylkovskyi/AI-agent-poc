import json
from datetime import datetime

from app.invoke_agent import invoke_agent
from logger.cust_logger import logger, set_files_message_color, format_log_message
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Agent PoC")

set_files_message_color("purple")  # Set log message color for this file to 'purple'

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://vvasylkovskyi.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    # unless described (error) logging is in {"timestamp": "YYYY-MM-DDTHH:MM:SS.MS", "uuid": "", "op": ""} format,
    # {timestamp, designated uuid, and what operation was done}

    await websocket.accept()
    user_uuid = None  # Placeholder for the conversation UUID
    try:
        while True:
            data = await websocket.receive_text()  # Receive message from client
            # Log the received data in {"timestamp": "YYYY-MM-DDTHH:MM:SS.MS", "uuid": "", "received": {"uuid": "", "init": bool}} format
            logger.info(format_log_message(f"Received from client: {json.loads(data)}"))

            try:
                # parse the data extracting the UUID and Message and if its the first message of the conversation
                payload = json.loads(data)
                user_uuid = payload.get("uuid")
                message = payload.get("message")
                init = payload.get("init", False)

                # If it's the first message, log the conversation initialization process
                if init:
                    logger.info(
                        format_log_message(
                            f"Initializing ws with client. UUID: {user_uuid}"
                        )
                    )
                else:
                    if message:
                        # If a message is provided, invoke the LangGraph, websocket for send, user message, and passing conversation ID
                        await invoke_agent(websocket, message, user_uuid)
            except json.JSONDecodeError as e:
                logger.error(format_log_message(f"JSON decoding error: {e}"))
    except Exception as e:
        # Catch all other unexpected exceptions and log the error
        logger.error(format_log_message(f"Unexpected error: {e}"))
    finally:
        # before the connection is closed, check if its already closed from the client side before trying to close from our side
        if user_uuid:
            logger.info(format_log_message(f"Closing connection. UUID: {user_uuid}"))
        try:
            await websocket.close()
        except RuntimeError as e:
            # uncaught connection was already closed error
            logger.error(
                format_log_message(
                    f"WebSocket close error: {e}. Connection was already closed."
                )
            )


@app.get("/health-check")
async def health_check():
    return {"status": "healthy2"}
