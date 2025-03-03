import os
import yaml
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ApiConfig:
    def __init__(self, default_config_file_path: str, api_desc_file_path: str):
        self.default_config_file_path: str = default_config_file_path
        self.api_desc_file_path: str = api_desc_file_path
        self.config_string: str = None
        self.config_keys: str = None
        self.api_desc: str = None
        logger.debug("ApiConfig class initialized with default config file: %s and API description file %s",
                     self.default_config_file_path, self.api_desc_file_path)

    def read_api_desc(self) -> str:
        logger.info("Reading API description file %s", self.api_desc_file_path)
        if self.api_desc is not None:
            logger.info("API description already read. Returning the same.")
            return self.api_desc
        try:
            if not os.path.exists(self.api_desc_file_path):
                logger.error("API description file %s not found.",
                            self.api_desc_file_path)
                return None
            with open(self.api_desc_file_path, 'r') as file:
                api_desc = file.read()
                if not api_desc:
                    raise ValueError(f"API description file {self.api_desc_file_path} is empty.")
                self.api_desc = api_desc
                return self.api_desc
        except Exception as e:
            logger.error("Error when trying to read API description file %s. Exception: %s",
                         self.api_desc_file_path, e)
            raise e

    def read_api_config(self) -> str:
        logger.info("Reading API config file %s", self.default_config_file_path)
        if self.config_string is not None:
            logger.info("API config already read. Returning the same.")
            return self.config_string
        try:
            if not os.path.exists(self.default_config_file_path):
                logger.info("API config file %s not found. Moving to next step.", self.default_config_file_path)
                return None
            with open(self.default_config_file_path, 'r') as file:
                try:
                    data = yaml.safe_load(file)
                    if data is None:
                        logger.info("No content in API config file %s. Moving to next step.",
                                    self.default_config_file_path)
                        return None

                    config_string = ""
                    for key, value in data.items():
                        config_string += f"{key}: {value}\n"
                    self.config_string = config_string.strip()
                    logger.debug("API config: %s", self.config_string)
                    return self.config_string
                except yaml.YAMLError as e:
                    logger.error("Error parsing YAML file %s. Exception: %s", self.default_config_file_path, e)
                    raise e
        except Exception as e:
            logger.error("Error when trying to read API config file %s. Exception: %s",
                         self.default_config_file_path, e)
            raise e

    def read_api_config_keys(self) -> str:
        logger.info("Reading API config keys from file %s", self.default_config_file_path)
        if self.config_keys is not None:
            logger.info("API config keys already read. Returning the same.")
            return self.config_keys
        try:
            if not os.path.exists(self.default_config_file_path):
                logger.info("API config file %s not found. Moving to next step.", self.default_config_file_path)
                return None
            with open(self.default_config_file_path, 'r') as file:
                try:
                    data = yaml.safe_load(file)
                    if data is None:
                        logger.info("No content in API config file %s. Moving to next step.",
                                    self.default_config_file_path)
                        return None
                    keys = list(data.keys())
                    keys_string = ",".join(keys)
                    self.config_keys = keys_string
                    logger.debug("API config keys: %s", keys_string)
                    return keys_string
                except yaml.YAMLError as e:
                    logger.error("Error parsing YAML file %s. Exception: %s", self.default_config_file_path, e)
                    raise e
        except Exception as e:
            logger.error("Error when trying to read API config file %s. Exception: %s",
                         self.default_config_file_path, e)
            raise e
