from fastapi import FastAPI, WebSocket
from app.agent import Agent
from langchain_core.messages import AIMessage
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Agent PoC")
agent = Agent()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
            config = {"configurable": {"thread_id": str(id(websocket))}}
            agent.chat(message, language, config)
            for chunk, metadata in agent.agent.stream(
                {"messages": message, "language": language},
                config,
                stream_mode="messages",
            ):
                if isinstance(chunk, AIMessage):  # Filter to just model responses
                    print(chunk.content, end="|")
                    await websocket.send_text(chunk.content)
 
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.get("/health-check")
async def health_check():
    return {"status": "healthy2"}