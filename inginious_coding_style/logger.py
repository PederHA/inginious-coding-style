import logging
import sys

try:
    # try to use Python 3.9's cache decorator
    # TODO: test on python3.9
    from functools import cache  # type: ignore
except ImportError:
    from functools import lru_cache, partial

    cache = partial(lru_cache, None)


@cache()
def get_logger() -> logging.Logger:
    # We just copy the logging style of INGInious here, because
    # plugins load before the standard loggers are instantiated.
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger = logging.getLogger("inginious.plugins.inginious_coding_style")
    logger.addHandler(ch)
    return logger
