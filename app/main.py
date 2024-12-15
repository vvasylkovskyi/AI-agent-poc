from fastapi import FastAPI
from app.agent import Agent
from pydantic import BaseModel

# Define the request body model
class ChatRequest(BaseModel):
    message: str  # This field will be required in the JSON body

app = FastAPI(title="AI Agent PoC")
agent = Agent()  # Initialize agent when app starts

@app.get("/health-check")
async def health_check():
    return {"status": "healthy2"}

@app.post("/chat")
async def chat(request: ChatRequest):
    language = "English"
    config = {"configurable": {"thread_id": "abc123"}}
    response = agent.chat(request.message, language, config)
    return { "respose": response }