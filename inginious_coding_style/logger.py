import logging
from functools import lru_cache


@lru_cache(None)
def get_logger() -> logging.Logger:
    # We just copy the logging style of INGInious here, because
    # plugins are loaded before the INGInious logger is configured.
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger = logging.getLogger("inginious.plugins.inginious_coding_style")
    logger.addHandler(ch)
    return logger
