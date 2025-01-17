import json

from invoke_agent import invoke_agent
from logger.cust_logger import logger, set_files_message_color, format_log_message
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from pydantic import BaseModel
from agent_core.agent_factory import AgentFactory
from agent_core.agent_factory import AgentType, AgentFactory

app = FastAPI(title="AI Agent PoC")

set_files_message_color("purple")  # Set log message color for this file to 'purple'

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://vvasylkovskyi.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CompletionRequest(BaseModel):
    prompt_key: str
    template_args: Dict[str, Any]


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


@app.post("/completions")
async def completions(request: CompletionRequest):
    """
    Endpoint for generating completions using template-based prompts.

    Expected request body:
    {
        "prompt_key": "linear_ticket",
        "template_args": {
            "project": "My Project",
            "issue_type": "feature",
            "description": "Add new authentication flow",
            "input": "Additional context about the feature"
        }
    }
    """
    try:
        agent = AgentFactory().create_agent(AgentType.ContentGeneratorAgent)
        response = await agent.invoke_with_template(
            request.prompt_key, request.template_args
        )
        return {"completion": response}

    except Exception as e:
        logger.error(format_log_message(f"Error in completions endpoint: {str(e)}"))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health-check")
async def health_check():
    return {"status": "healthy2"}
