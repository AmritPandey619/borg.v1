import yaml
import pprint
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ConfigReader:
    _instance: 'ConfigReader' = None
    config: dict

    def __new__(cls) -> 'ConfigReader':
        if cls._instance is None:
            cls._instance = super(ConfigReader, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        logger.info("Reading config...")
        with open("config.yml", "r") as file:
            self.config = yaml.safe_load(file)
        logger.info("Configuration loaded from config.yml")
        self.print_config()
        logger.debug("ConfigReader initialization complete.")

    def get_config(self, name: str) -> str:
        value = self.config.get(name)
        logger.debug(f"Config value for {name}: {value}")
        return value

    def get_int_config(self, name: str) -> int:
        value_str = self.get_config(name)
        if value_str is not None:
            try:
                value = int(value_str)
                logger.debug(f"Int config value for {name}: {value}")
                return value
            except ValueError as ve:
                logger.error(f"Could not parse int value for {name}: {value_str}.")
                raise ve
        return None

    def get_float_config(self, name: str) -> float:
        value_str = self.get_config(name)
        if value_str is not None:
            try:
                value = float(value_str)
                logger.debug(f"Float config value for {name}: {value}")
                return value
            except ValueError as ve:
                logger.error(f"Could not parse float value for {name}: {value_str}.")
                raise ve
        return None

    def get_bool_config(self, name: str) -> bool:
        value = self.config.get(name)
        if isinstance(value, bool):
            logger.debug(f"Bool config value for {name}: {value}")
            return value
        if isinstance(value, str):
            if value.lower() == 'true':
                logger.debug(f"Bool config value for {name}: True")
                return True
            if value.lower() == 'false':
                logger.debug(f"Bool config value for {name}: False")
                return False
        if isinstance(value, int):
            if value == 1:
                logger.debug(f"Bool config value for {name}: True")
                return True
            if value == 0:
                logger.debug(f"Bool config value for {name}: False")
                return False
        logger.warning(f"Could not parse boolean value for {name}: {value}. Returning False.")
        return False

    def get_or_default(self, name: str, default_value: str) -> str:
        value = self.get_config(name)
        if value is None:
            self.config[name] = default_value
            logger.debug(f"Config value for {name} not found or null, assigning default value: {default_value}")
            return default_value
        return value

    def get_or_default_int(self, name: str, default_value: int) -> int:
        value = self.get_int_config(name)
        if value is None:
            self.config[name] = default_value
            logger.debug(f"Config value for {name} not found or null, assigning default value: {default_value}")
            return default_value
        return value

    def get_or_default_float(self, name: str, default_value: float) -> float:
        value = self.get_float_config(name)
        if value is None:
            self.config[name] = default_value
            logger.debug(f"Config value for {name} not found or null, assigning default value: {default_value}")
            return default_value
        return value

    def get_or_default_bool(self, name: str, default_value: bool) -> bool:
        value = self.get_bool_config(name)
        if value is None:
            self.config[name] = default_value
            logger.debug(f"Config value for {name} not found or null, assigning default value: {default_value}")
            return default_value
        return value

    def print_config(self) -> None:
        """Prints the configuration loaded from config.yml."""
        logger.info("Configuration:")
        pprint.pprint(self.config, indent=2, width=80, depth=None)
