import yaml
import logging

def setup_logger(name: str) -> logging.Logger:
    """Sets up a logger with the specified name and level."""
    with open("config.yml", "r") as file:
        config = yaml.safe_load(file)
        level = config.get("LOG_LEVEL")

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.hasHandlers():
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logger(__name__)
