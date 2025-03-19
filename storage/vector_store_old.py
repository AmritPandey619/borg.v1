from typing import List, Any
import httpx
from langchain_community.document_loaders import TextLoader
from langchain.tools.retriever import create_retriever_tool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from config.config_reader import ConfigReader
from utils.logger import setup_logger

logger = setup_logger(__name__)

class VectorStore:
    basr_url_embedding: str
    api_key_embedding: str
    embedding_model_name: str
    persist_dir: str
    collection_name: str
    vector_store: Any
    retriever: Any

    def __init__(self, collection_name: str):
        logger.info("Initializing VectorStore...")
        config_reader = ConfigReader()
        self.embedding_provider = config_reader.get_config("EMBEDDING_PROVIDER")
        self.basr_url_embedding = config_reader.get_config("EMBEDDING_API_BASE")
        self.api_key_embedding = config_reader.get_config("EMBEDDING_API_KEY")
        self.llmgw_workspace = config_reader.get_config("LLMGW_WORKSPACE")
        self.embedding_model_name = config_reader.get_config("EMBEDDING_MODEL_NAME")
        self.chunk_size = config_reader.get_or_default_int("CHUNK_SIZE", 1000)
        self.chunk_overlap = config_reader.get_or_default_int("CHUNK_OVERLAP", 200)
        self.vector_store: Chroma = None
        self.retriever = None
        self.collection_name = collection_name
        if self.embedding_provider == "OLLAMA":
            self.embedding_func = OllamaEmbeddings(model=self.embedding_model_name,
                                      base_url=self.basr_url_embedding)
        elif self.embedding_provider == "OPENAI":
            self.embedding_func = OpenAIEmbeddings(model=self.embedding_model_name,
                                      base_url=self.basr_url_embedding)
        elif self.embedding_provider == "LLMGW":
            self.embedding_func = OpenAIEmbeddings(http_client=httpx.Client(
                headers={'api-key': self.api_key_embedding,
                         'workspacename': self.llmgw_workspace}
                         ),
                         model=self.embedding_model_name,
                                      base_url=self.basr_url_embedding)
        logger.debug("Embeddings model: %s, base_url: %s", self.embedding_model_name,
                     self.basr_url_embedding)

        self.persist_dir: str = config_reader.get_config("PERSIST_DIRECTORY")
        self.vector_store = Chroma(collection_name=collection_name,
                                   embedding_function=self.embedding_func,
                                   persist_directory=self.persist_dir)

        logger.debug("Chroma DB client initialized with persist_dir: %s and collection name %s",
                     self.persist_dir, collection_name)
        logger.info("VectorStore initialization complete.")

    def load_document(self, data_file: str) -> None:
        logger.info("Loading document to collection: %s", self.collection_name)
        loader = TextLoader(data_file)
        docs = loader.load()
        documents = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
        ).split_documents(docs)
        logger.debug("Document split into %s chunks", len(documents))

        _ = self.vector_store.add_documents(documents=documents)
        #collection = self.vector_store.get()

        logger.debug("Document added to vector store.")

        self.retriever = self.vector_store.as_retriever()
        logger.info("Retriever created.")

    def get_retriever_tool(self, tool_name: str, tool_desc: str) -> Any:
        logger.info("Creating retriever tool: %s", tool_name)
        retriever_tool = create_retriever_tool(
            self.retriever,
            tool_name,
            tool_desc,
        )
        logger.info("Retriever tool created: %s", tool_name)
        return retriever_tool

    def retrieve(self, query: str) -> List[Any]:
        retrieved_docs = self.vector_store.similarity_search(query,k=2)
        logger.debug("Search results: %s", retrieved_docs)
        return retrieved_docs
