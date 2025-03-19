from pydantic import BaseModel
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from agents.agent import Agent
from llm.llm import LLM
from utils.logger import setup_logger
from storage.vector_store_old import VectorStore
from config.api_config_reader import ApiConfig
from config.config_reader import ConfigReader
import yaml
from typing import List
from pydantic import BaseModel, Field

logger = setup_logger(__name__)

PROMPT_FILE_VECTOR_SEARCH = "agents/retrieve/prompt_vector_search.txt"
PROMPT_FILE_LLM_QUERY = "agents/retrieve/prompt_llm_query.txt"

class keyElement(BaseModel):
    elements: List
    #action: str


#class StepList(BaseModel):
 #   steps: List[Step] = Field(..., description="List of steps to be executed")

class RetrieveAgent(Agent):
    llm: LLM

    def __init__(self, llm: LLM):
        super().__init__()
        self.llm = llm
        config_reader = ConfigReader()
        self.llm_query = config_reader.get_or_default_bool("LLM_QUERY", False)
        logger.info("RetrieveAgent initialized.")

    def is_documentation_query_llm(self, query: str) -> bool:
        """Uses LLM to determine if the user is asking for documentation help."""
        prompt = f"""
        Classify the intent of the following query as either 'documentation' or 'test_case':
        Query: "{query}"
        
        If the query is asking about Robot Framework syntax, keywords, or usage, return 'documentation'.
        Otherwise, return 'test_case'.
        """
        response = self.llm.chat_completion(prompt=prompt)
        return "documentation" in response.lower()

    def read_prompt(self, prompt_file) -> str:
        return open(prompt_file).read().strip()

    def retrieve(self, state: dict, config: dict) -> dict:
        """
        Invokes the retrieve agent to search and retrieve chunks from the vector store.
        The user question is enhanced before executing the search.
        Args:
            state (messages): The current state
            config (dict): The configuration dictionary
        Returns:
            dict: The updated state with the agent response appended to messages
        """
        logger.info("Starting retrieve method...")
        logger.info("---CALL RETRIEVE AGENT---")

        vector_store: VectorStore = config["configurable"]["vdb"]
        api_config_file: str = config["configurable"]["api_config_file"]
        api_desc_file: str = config["configurable"]["api_desc_file"]
        messages = state["messages"]
        question = messages[0].content
        helpRequest = self.is_documentation_query_llm(question)
        # messages is something like: [HumanMessage(content='Print the REST request to create a user named
        # himanshu singh who has a mobile number of 99999999 and prefers sms notification in german
        # language', additional_kwargs={}, response_metadata={}, id='c62addda-9645-489e-9e08-1665126d9adc')]
        search_query = None

        api_config_keys = ""
        if api_config_file is not None:
            api_config = ApiConfig(default_config_file_path=api_config_file, api_desc_file_path=api_desc_file)
            api_config_keys = api_config.read_api_config_keys()

        if self.llm_query:
            logger.info("LLM query flag is enabled. Query LLM to get keywords for vector search.")

            output_parser = PydanticOutputParser(pydantic_object=keyElement)

            prompt = PromptTemplate.from_template(
                self.read_prompt(PROMPT_FILE_LLM_QUERY))

            logger.debug("Query LLM with prompt: %s and question %s and default api config %s",
                        prompt, question, api_config_keys)

            formatted_prompt = prompt.format(question=question)
            logger.debug("FORMATTED prompt: %s",formatted_prompt)
            response = self.llm.chat_completion(prompt=formatted_prompt)
            logger.debug("LLM RESPONSE1 : %s",response)
            llm_response = output_parser.parse(response)
            logger.debug("LLM RESPONSE : %s",llm_response)

            #for item in llm_response.elements:
             #   logger.debug(" ITEM   : %s",item)
           # logger.debug("LLM query response: High Level Keywords %s; Low Level Keywords: %s",
                  #       llm_response.high_level_keywords, llm_response.low_level_keywords)

          #  search_query = ", ".join(llm_response.high_level_keywords) + ", " + ", ".join(
            #    llm_response.low_level_keywords)
            logger.debug("LLM query response: %s", response)
         #   logger.debug("Formatted Output response: %s", llm_response)
            """
            # Chain
            # If structured output is not being used, use StrOutputParser
            # rag_chain = prompt | self.llm | StrOutputParser()
            try:
                llm_response = llm_response.lstrip("```json\n").rstrip("\n```")
                keywords_data = json.loads(llm_response)
                hlkeywords = keywords_data.get("high_level_keywords", [])
                llkeywords = keywords_data.get("low_level_keywords", [])
                search_query = ", ".join(hlkeywords) + ", " + ", ".join(llkeywords)
            except json.JSONDecodeError as e:
                logger.warning("Response from LLM is not a valid json. Error: %s", e)
            """
            logger.info("LLM query done. Proceeding to vector search.")
        else:
            # Extract the content of the message and enhance it to have better
            # results from the vector search
            prompt_template = PromptTemplate.from_template(self.read_prompt(
                PROMPT_FILE_VECTOR_SEARCH))
            search_query = prompt_template.format(user_message=messages[0].content,
                                            api_config_keys=api_config_keys)

        logger.debug("Invoking vector search with query: %s", llm_response.elements)
      #  search_Element_List =   ["Custom Data","Create Profile","Delete Profile","Set Lifecycle"]
        response2: str = ""
        for item in llm_response.elements:
            key_value_pairs = [(key, value) for key, value in item.items()]
            logger.debug("STEP1  = %s",key_value_pairs)
            queryString: str = " ".join([key_value_pairs[0][1]])
            logger.debug("STEP2  = %s",queryString)
            docs_content = vector_store.retrieve(queryString)
            response1 = "\n\n".join(doc.page_content for doc in docs_content)
  
            logger.debug("STEP333  = %s",response1)
            response2 = "\n\n".join([response1,response2])
      #  logger.info("Reading config...")
       # config: dict
        #with open("queryFile.yml", "r") as file:
         #   config = yaml.safe_load(file)
        #logger.info("Configuration loaded from config.yml")
       # self.print_config()
        #logger.debug("ConfigReader initialization complete.")
        #query1 = config.get("Key1")
        #logger.debug("Invoking vector search with query: %s", query1)
       # docs_content1 = vector_store.retrieve(query1)

       # response = "\n\n".join(doc.page_content for doc in docs_content)
        #query2 = config.get("Key2")
        #logger.debug("Invoking vector search with query: %s", query2)
       # docs_content2 = vector_store.retrieve(query2)
       # response1 = "\n\n".join(doc.page_content for doc in docs_content1)
       # response2 = "\n\n".join(doc.page_content for doc in docs_content2)        
        #response = "\n\n".join([response1,response2])
        logger.info("Vector search complete. Exiting retrieve method.")

        # We return a list, because this will get added to the existing list
        return {"messages": [response2], 'helpRequest':helpRequest}
