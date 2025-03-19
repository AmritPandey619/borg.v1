from langchain_core.prompts import PromptTemplate
from llm.llm import LLM
from agents.agent import Agent
from utils.logger import setup_logger
from config.api_config_reader import ApiConfig

PROMPT_FILE = "agents/generate/prompt.txt"

logger = setup_logger(__name__)

class GenerateAgent(Agent):
    llm: LLM
    def __init__(self, llm: LLM):
        super().__init__()
        self.llm = llm
        logger.info("GenerateAgent initialized.")

    def read_prompt(self) -> str:
        return open(PROMPT_FILE).read().strip()

    def generate(self, state: dict, config: dict) -> dict:
        """
        Generate answer
        Args:
            state (messages): The current state
        Returns:
            dict: The updated state with generated response
        """
        logger.info("Starting generate method...")
        logger.info("---CALL GENERATE AGENT---")
        helpRequest = state["helpRequest"]
        messages = state["messages"]
        question = messages[0].content
        last_message = messages[-1]
        docs = last_message.content
        logger.info("---STEP 10-- %s",docs)
        if helpRequest:
            prompt = f"Here is the relevant Robot Framework documentation: {docs}\nExplain this in simple terms."
            response = self.llm.chat_completion(prompt=prompt)

            return {"messages": [response]}
      #  api_config_file: str = config["configurable"]["api_config_file"]
       # api_desc_file: str = config["configurable"]["api_desc_file"]
        #api = ApiConfig(default_config_file_path=api_config_file,
        #    api_desc_file_path=api_desc_file)
        #api_desc = api.read_api_desc()
        #api_config = None
        #if api_config_file is not None:
        #   api_config = api.read_api_config()
        #lse:
        #   api_config = "No default config provided"

        # Prompt
        logger.info("---STEP 11--")
        prompt = PromptTemplate.from_template(self.read_prompt())
        logger.info("---STEP 12--")
        # Post-processing
       # def format_docs(docs):
        #    return "\n\n".join(doc.page_content for doc in docs)

        logger.debug("Query LLM with prompt: %s and question %s and default config %s and context %s",
                     prompt, question, docs)
        logger.debug("Query LLM with prompt: %s ",prompt)
        logger.debug("Query LLM with Question: %s ",question)
        logger.debug("Query LLM with Document: %s ",docs)
       # formatted_prompt = prompt.format(context=docs, question=question,
        #                                 api_config=api_config)
        formatted_prompt = prompt.format(context=docs, question=question)
        logger.debug("Query LLM with formatted_prompt: %s ",formatted_prompt)
        response = self.llm.chat_completion(prompt=formatted_prompt)
        logger.debug("Generated response: %s", response)
        logger.info("Generate method complete.")
        return {"messages": [response]}
