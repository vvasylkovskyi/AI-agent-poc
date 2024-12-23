# LangGraph AI Agent

This is a proof of concept for a LangGraph AI Agent. Essentially we are using LangGraph to define the workflow of the agent and then we are using FastAPI to expose a websocket endpoint for the client to interact with the agent.

The agent is composed of the graph with containing Tools and LLM nodes. it begins by asking the LLM to perform the reasoning and once the LLM has performed the reasoning, it will call the Tools to get the data. Once the Tools have been called, the agent will call the LLM again to perform the reasoning again with the new data. This process repeats until the agent has performed the reasoning enough times or the LLM has run out of tokens.

![alt text](./docs/graph.png)

## Install Dependencies

```sh
make install
```

## Run the server

```sh
make run
```

## Start LangGraph Server

Make sure to install LangGraph dependencies first.

```sh
pip install --upgrade "langgraph-cli[inmem]"
```

or if using MAC:

```sh
brew install langgraph-cli
```

Run LangGraph server

```sh
make langgraph
```

## Run server with docker

```sh
cd server
docker build -t ai-chat-server .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key_here ai-chat-server
```

## Setup Google Cloud Vertex AI

First to make Google Vertex AI work, you need to do the following:

1. Create a project in Google Cloud to work on
2. Setup Authentication with `gcloud`
3. Create Service Account and download the key
4. Create Google Cloud Storage Bucket
5. Setup Service Accounts with proper roles
6. Enable the necessary APIs

### Create a project in Google Cloud

Follow the step-by-step from `https://cloud.google.com/vertex-ai/generative-ai/docs/reasoning-engine/set-up`

Create a project and make sure that the billing is enabled.

The rest can be done from the `gcloud` CLI.

### Install gcloud (if not installed)

```sh
brew install google-cloud-sdk
```

### Authenticate to Google Cloud

```sh
gcloud auth login
gcloud config set project <project_name>
```

### Create Service Account and download the key

```sh
# Create service account
gcloud iam service-accounts create vertex-ai-sa \
    --description="Service account for Vertex AI" \
    --display-name="Vertex AI Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding <project_id> \
    --member="serviceAccount:vertex-ai-sa@<project_id>.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create vertex-ai-key.json \
    --iam-account=vertex-ai-sa@<project_id>.iam.gserviceaccount.com
```

Update your `.env` file with the `GOOGLE_APPLICATION_CREDENTIALS` environment variable.

```sh
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/vertex-ai-key.json"
```

### Create Google Cloud Storage Bucket

Vertex AI Reasoning Engine needs a bucket to store the model and the data.

```sh
gsutil mb -l <location> gs://<bucket_name>
```

### Setup Service Accounts with proper roles

```sh
# Add Storage Admin role
gcloud projects add-iam-policy-binding vertex-ai-project-445621 \
    --member="serviceAccount:vertex-ai-sa@vertex-ai-project-445621.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Add Vertex AI User role
gcloud projects add-iam-policy-binding vertex-ai-project-445621 \
    --member="serviceAccount:vertex-ai-sa@vertex-ai-project-445621.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

### Enable the necessary APIs

```sh
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage-component.googleapis.com
```

### Add dependency to langchain-google-vertexai

```sh
pip install langchain-google-vertexai
```

## Push to docker hub

```sh
docker tag ai-chat-server your_dockerhub_username/ai-chat-server
docker push your_dockerhub_username/ai-chat-server
```
