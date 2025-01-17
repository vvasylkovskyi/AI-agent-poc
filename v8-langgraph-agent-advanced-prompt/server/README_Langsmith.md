# How to setup LangSmith

Add `.env` file in the root directory of the project

```sh
# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="key"
LANGCHAIN_PROJECT="relyio"
```

## Install LangSmith

```sh
poetry add langsmith
```
