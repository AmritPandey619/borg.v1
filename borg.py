import argparse
from typing import Dict, Any
from langgraph.graph import START, StateGraph, END
from agents.retrieve.retrieve import RetrieveAgent
from agents.generate.generate import GenerateAgent
from agents.agent_state import AgentState
from llm.llm import LLM
from config.config_reader import ConfigReader
from storage.vector_store import VectorStore
from utils.logger import setup_logger
 
logger = setup_logger(__name__)

class Borg:
    def __init__(self):
        logger.info("\033[92mBorg: Initializing...\033[0m")
        self.config_reader = ConfigReader()
        self.llm = LLM()
        self.vector_store = VectorStore(collection_name="api_doc")
        logger.info("\033[92mBorg: All systems online. Awaiting mission parameters.\033[0m")

    def load_documents(self, data_file: str) -> None:
        logger.info("Data file %s will be loaded in vector store.",data_file)
        self.vector_store.load_document(data_file=data_file)
        logger.info("Data file %s loaded in vector store.",data_file)

    def __del__(self):
        logger.info("\033[91mBorg: Shutting down. All systems offline.\033[0m")
        logger.info("\033[91mBorg: I... Will... Be... Back\033[0m")

    def create_graph(self) -> StateGraph:
        logger.info("Creating graph...")
        # Define a new graph
        workflow = StateGraph(AgentState)
        retrieve_agent = RetrieveAgent(self.llm)
        generate_agent = GenerateAgent(self.llm)
        #retrieve_agent = RetrieveAgent(None)
        # Define the nodes we will cycle between
        workflow.add_node("retrieve", retrieve_agent.retrieve)
        workflow.add_node("generate", generate_agent.generate)

        # Call retrieve node to get the documents
        workflow.add_edge(START, "retrieve")

        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("retrieve", END)
        workflow.add_edge("generate", END)
        

        # Compile
        graph = workflow.compile()
        logger.info("Graph creation complete.")
        return graph

    def execute_graph(self, graph: StateGraph, vdb: VectorStore, 
                      api_config_file: str,
                      api_desc_file: str,
                      inputs: Dict[str, Any]) -> str:
        logger.info("Executing graph...")
        final_response: str = None
        for output in graph.stream(inputs, {"configurable":
                                            {"vdb": vdb, 
                                             "api_config_file": api_config_file,
                                             "api_desc_file": api_desc_file}}
                                            ):
            final_response = ""
            for key, value in output.items():
                logger.debug("Output from node '%s':", key)
                logger.debug(value)
                final_response += value.get('messages', [''])[0]
        logger.info("Graph execution complete.")
        return final_response

    def execute(self, query: str, api_config_file: str, api_desc_file: str) -> str:
        inputs = {
            "messages": [
                ("user", query),
            ]
        }
        logger.info("Query from user: %s", inputs)

        graph = self.create_graph()
        return self.execute_graph(graph, self.vector_store, api_config_file, api_desc_file, inputs)

def main():
    parser = argparse.ArgumentParser(description="Borg: Query API docs.")
    parser.add_argument('-a', '--add-document', type=str, help='Add a document to the vector store')
    parser.add_argument('-q', '--query', type=str, help='Ask Borg to answer a query about APIs')
    parser.add_argument('-c', '--api-config', type=str, help='Optional. The path of yml file with default API configs')
    parser.add_argument('-d', '--api-desc', type=str, help='Optional. The path of file with API description')

    args = parser.parse_args()

    if not args.add_document and not args.query:
        parser.error("""At least one of --add-document or --query must be provided. Use --help for more information.""")

    borg = Borg()

    if args.add_document:
        borg.load_documents(args.add_document)

    if args.query:
        graph_response = borg.execute(args.query, args.api_config, args.api_desc)
        logger.info("Final response: %s", graph_response)

if __name__ == "__main__":
    main()
