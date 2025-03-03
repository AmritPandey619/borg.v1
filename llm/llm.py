import os
import httpx
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from openai import OpenAI
from config.config_reader import ConfigReader
from utils.logger import setup_logger

logger = setup_logger(__name__)

class LLM:
    llm_provider: str
    model_name: str
    llm: None

    def __init__(self):
        logger.info("Initializing LLM...")
        config_reader = ConfigReader()
        self.llm_provider = config_reader.get_config("LLM_PROVIDER")
        self.model_name = config_reader.get_config("MODEL_NAME")
        self.api_key = config_reader.get_config("OPEN_AI_API_KEY")
        self.base_url = config_reader.get_config("OPEN_AI_API_BASE")
        self.google_api_key = config_reader.get_config("GOOGLE_API_KEY")
        if self.api_key is not None:
            os.environ["OPENAI_API_KEY"] = self.api_key
        if self.base_url is not None:
            os.environ["OPENAI_API_BASE"] = self.base_url
        if self.google_api_key is not None:
            os.environ["GOOGLE_API_KEY"] = self.google_api_key
        self.llmgw_workspace = config_reader.get_config("LLMGW_WORKSPACE")
        self.temperature = config_reader.get_or_default_int("TEMPERATURE", 1)
        self.top_p = config_reader.get_or_default_float("TOP_P", 0.9)
        self.timeout = config_reader.get_or_default_int("TIMEOUT", None)
        self.max_retries = config_reader.get_or_default_int("MAX_RETRIES", None)
        self.max_tokens = config_reader.get_or_default_int("MAX_TOKENS", None)
        self.init_llm()
        logger.debug("LLM initialized with provider: %s, model: %s", self.llm_provider,
                     self.model_name)

    def init_llm(self, streaming: bool = False):
        logger.info("Getting LLM with streaming: %s", streaming)
        if self.llm_provider == "OPENAI" or self.llm_provider == "OPENAILIKE":
            logger.debug("Using OpenAI API")
            self.llm = ChatOpenAI(model=self.model_name, streaming=streaming,
                             temperature=self.temperature,
                             top_p=self.top_p,
                             timeout=self.timeout,
                             max_retries=self.max_retries,
                             max_tokens=self.max_tokens)
        elif self.llm_provider == "GEMINI":
            logger.debug("Using Gemini API")
            self.llm = ChatGoogleGenerativeAI(model=self.model_name,
                                         streaming=streaming,
                                         temperature=self.temperature,
                                         top_p=self.top_p,
                                         timeout=self.timeout,
                                         max_retries=self.max_retries,
                                         max_tokens=self.max_tokens)
        elif self.llm_provider == "LLMGW":
            logger.debug("Using NOKIA LLMGW API")
            self.llm = OpenAI(
                timeout=self.timeout,
                max_retries=self.max_retries,
                api_key="NONE",
                base_url=self.base_url,
                http_client=httpx.Client(
                    headers={
                        'api-key': self.api_key,
                        'workspacename': self.llmgw_workspace,
                    }
                )
            )
        logger.info("LLM obtained: %s", self.llm)

    def get_llm(self):
        return self.llm

    def chat_completion(self, prompt: str):
        response = None
        messages = [
            {"role": "user", "content": prompt},
        ]

        if self.llm_provider == "OPENAI" or self.llm_provider == "OPENAILIKE":
            logger.info("Invoking chat completion for OPENAI")
            raw_response = self.llm.invoke(prompt,
                            model=self.model_name,
                            temperature=self.temperature,
                            max_tokens=self.max_tokens,
                            top_p=self.top_p,
                            timeout=self.timeout
                            )
            logger.debug("LLM response: %s", raw_response)
            response = raw_response.content
        elif self.llm_provider == "GEMINI":
            logger.info("Invoking chat completion for GEMINI")
            raw_response = self.llm.invoke(prompt)
            logger.debug("LLM response: %s", raw_response)
            response = raw_response.content
        elif self.llm_provider == "LLMGW":
            llm: OpenAI = self.llm
            logger.info("Invoking chat completion for OPENAI")
            raw_response = llm.chat.completions.create(messages=messages,
                                             model=self.model_name,
                                             temperature=self.temperature,
                                             max_tokens=self.max_tokens,
                                             top_p=self.top_p,
                                             timeout=self.timeout
                                             )
            logger.debug("LLM response: %s", raw_response)
            response = raw_response.choices[0].message.content
        logger.info("Chat completion complete.")
        return response
