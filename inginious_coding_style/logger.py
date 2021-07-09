from logging import Logger, getLogger
from functools import lru_cache


@lru_cache(None)
def get_logger() -> Logger:
    return getLogger("inginious.plugins.inginious_coding_style")
