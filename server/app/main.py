from app.agent import Agent
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage

app = FastAPI(title="AI Agent PoC")
agent = Agent()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://vvasylkovskyi.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            language = "English"
            config = {
                "configurable": {"thread_id": str(id(websocket)), "recursion_limit": 2}
            }

            # Add the human message first
            response = {
                "messages": [
                    {"content": message, "origin": "human"},
                ]
            }
            await websocket.send_json(response)

            # Get and send AI response
            response = agent.chat(message, language, config)
            ai_response = {
                "messages": [
                    {
                        "content": msg.content,
                        "origin": "ai",
                    }
                    for msg in response["messages"]
                ]
            }
            await websocket.send_json(ai_response)

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@app.get("/health-check")
async def health_check():
    return {"status": "healthy2"}
