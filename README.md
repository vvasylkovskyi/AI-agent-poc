# AI-agent-poc

A proof of concept project using FastAPI.

## Requirements

- Python 3.8+
- Poetry
- Make

## Setup

## Before working on the project

```sh
# Environment Activation
source .venv/bin/activate

# Check Active Environment
# Should show path to your project's virtual environment
which python

# Create and activate virtual environment
make venv
source .venv/bin/activate  # (or .venv\Scripts\activate on Windows)

# Install dependencies
make install

# Run the server
make run

# Should show (venv) at the start of your prompt
# You can also run:
pip -V  # Should show pip from your virtual environment

```

## Run server with docker

```sh
cd server
docker build -t ai-chat-server .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key_here ai-chat-server
```

## Push to docker hub

```sh
docker tag ai-chat-server your_dockerhub_username/ai-chat-server
docker push your_dockerhub_username/ai-chat-server
```
