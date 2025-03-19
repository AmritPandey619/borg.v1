from posixpath import sep
from pydoc import Doc
from typing import List, Any
import httpx
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader
from langchain.tools.retriever import create_retriever_tool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_milvus import Milvus
#from pymilvus import connections, db, MilvusClient
from config.config_reader import ConfigReader
from utils.logger import setup_logger
# from storage.separator_chunking import SeparatorBasedChunker

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
        self.vector_store = None
        self.retriever = None
        self.chunker = None
        self.collection_name = collection_name

        #read embedding config
        self.embedding_provider = config_reader.get_config("EMBEDDING_PROVIDER")
        self.basr_url_embedding = config_reader.get_config("EMBEDDING_API_BASE")
        self.api_key_embedding = config_reader.get_config("EMBEDDING_API_KEY")
        self.embedding_model_name = config_reader.get_config("EMBEDDING_MODEL_NAME")
        self.llmgw_workspace = config_reader.get_config("LLMGW_WORKSPACE")
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

        #read vector store config
        self.vector_db_provider = config_reader.get_or_default("VECTOR_DB_PROVIDER",
                                                               "CHROMA_EMBEDDED")
        if self.vector_db_provider == "CHROMA_EMBEDDED":
            persist_dir: str = config_reader.get_config(
                "PERSIST_DIRECTORY")+"/"+self.collection_name
            self.vector_store = Chroma(collection_name=collection_name,
                            embedding_function=self.embedding_func,
                            persist_directory=persist_dir)
            logger.debug("Chroma DB client initialized with persist_dir: %s and collection name %s",
                     persist_dir, collection_name)
        elif self.vector_db_provider == "MILVUS":
            milvus_host = config_reader.get_or_default("MILVUS_HOST", "127.0.0.1")
            milvus_port = config_reader.get_or_default_int("MILVUS_PORT", 19530)
            milvus_db_name = config_reader.get_or_default("MILVUS_DB_NAME", "default")
            milvus_user = config_reader.get_or_default("MILVUS_USER", "root")
            milvus_password = config_reader.get_or_default("MILVUS_PASSWORD", "Milvus")
            #connect to Milvus
            try:
                #self.vector_store = connections.connect(host=milvus_host,
                #                        port=milvus_port, user=milvus_user,
                #                        password=milvus_password,
                #                        db_name=milvus_db_name)
                #self.vector_store = MilvusClient(uri="http://"+milvus_host+":"+milvus_port,
                #                                 user=milvus_user,
                #                                 password=milvus_password,
                #                                 db_name=milvus_db_name,
                #                                 timeout=30)
                milvus_connect_params = {"uri": "http://"+milvus_host+":"+str(milvus_port),
                                          "user":milvus_user,
                                          "password":milvus_password,
                                          "db_name":milvus_db_name,
                                          "timeout":30
                                          }
                self.vector_store = Milvus(collection_name=collection_name,
                                           embedding_function=self.embedding_func,
                                           connection_args=milvus_connect_params,
                                           auto_id=True)
            except Exception as e:
                logger.error("Could not connect to Milvus DB %s on %s:%s and user %s",
                             milvus_db_name, milvus_host, milvus_port,
                             milvus_user)
                raise e

        self.num_search_results = config_reader.get_or_default_int("NUM_SEARCH_RESULTS", 4)
        self.chunk_size = config_reader.get_or_default_int("CHUNK_SIZE", 1000)
        self.chunk_overlap = config_reader.get_or_default_int("CHUNK_OVERLAP", 200)
        self.separator = config_reader.get_or_default("SEPARATOR", "#####")
        self.chunking_strategy = config_reader.get_or_default("CHUNKER", "DEFAULT")
        if self.chunking_strategy == "DEFAULT":
            self.chunker = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size,
                                                          chunk_overlap=self.chunk_overlap)
        elif self.chunking_strategy == "SEPARATOR_BASED":
            self.chunker = SeparatorBasedChunker(separator=self.separator)

        logger.info("VectorStore initialization complete.")

    def load_document(self, data_file: str) -> None:
        loader = TextLoader(data_file)
        docs = loader.load()
        documents = self.chunker.split_documents(docs)
        logger.debug("Document split into %s chunks", len(documents))
        logger.info("Loading document to collection: %s", self.collection_name)
        _ = self.vector_store.add_documents(documents=documents)
        #collection = self.vector_store.get()
        self.retriever = self.vector_store.as_retriever()
        logger.info("Retriever created.")
        logger.debug("Document added to vector store.")

    def get_retriever_tool(self, tool_name: str, tool_desc: str) -> Any:
        logger.info("Creating retriever tool: %s", tool_name)
        retriever_tool = create_retriever_tool(
            self.retriever,
            tool_name,
            tool_desc,
        )
        logger.info("Retriever tool created: %s", tool_name)
        return retriever_tool

    def retrieve(self, query: str) -> List[Document]:
        if query is None:
            return []
        logger.info("\033[96mInvoking vector search with query: %s\033[0m", query)
        retrieved_docs = self.vector_store.similarity_search(
            query=query, k=self.num_search_results)
        logger.debug("\033[96mSearch results: %s\033[0m", retrieved_docs)
        return retrieved_docs

    def retrieve_multi(self, queries: List[str]) -> List[Document]:
        all_retrieved_docs = []
        for query in queries:
            if query is not None:
                logger.info("\033[96mInvoking vector search with query: %s\033[0m", query)
                retrieved_docs: List[Document] = self.vector_store.similarity_search(
                    query=query, k=self.num_search_results)
                logger.debug("\033[96mSearch results for query '%s': %s\033[0m", query, retrieved_docs)
                all_retrieved_docs.extend(retrieved_docs)
        return all_retrieved_docs
