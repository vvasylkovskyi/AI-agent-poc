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
            
            # Add the human message first
            response = {
                'messages': [
                    {'content': message, 'origin': 'human'},
                ]
            }
            await websocket.send_json(response)
            
            # Get and send AI response
            messages = agent.chat(message, language, config)
            ai_response = {
                'messages': [
                    {
                        'content': messages[-1].content,
                        'origin': 'ai',
                    }
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