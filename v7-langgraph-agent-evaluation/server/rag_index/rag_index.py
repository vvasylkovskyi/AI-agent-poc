from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.retrievers import BaseRetriever
from logger.cust_logger import logger, set_files_message_color, format_log_message

urls = [
    "https://lilianweng.github.io/posts/2023-06-23-agent/",
    "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
    "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
]


set_files_message_color("CYAN")  # Set color for logging in this function


class RagIndex:
    _instance = None  # Class attribute to store the singleton instance

    vectordb: Chroma
    persistence_path: str
    retriever: BaseRetriever

    def __new__(cls, *args, **kwargs):
        # Check if an instance already exists
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):  # Ensure __init__ is run only once
            self.initialized = True
            self.vectordb = None
            self.persistence_path = None
            self.retriever = None

    def update_index(self):
        docs = [WebBaseLoader(url).load() for url in urls]
        docs_list = [item for sublist in docs for item in sublist]
        logger.info(
            format_log_message(f"RAG Index docs_list {len(docs_list)} documents")
        )
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=100, chunk_overlap=50
        )
        doc_splits = text_splitter.split_documents(docs_list)

        # Add to vectorDB
        self.verctordb = Chroma.from_documents(
            documents=doc_splits,
            collection_name="rag-chroma",
            embedding=VertexAIEmbeddings(model_name="text-embedding-004"),
        )

        logger.info(
            format_log_message(
                f"RAG Index updated with {len(self.verctordb)} documents"
            )
        )
        self.retriever = self.verctordb.as_retriever()
