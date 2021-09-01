"""Module for filesystem functions."""

import shutil
from pathlib import Path
from typing import Iterator, Optional

from inginious.common.base import load_json_or_yaml, write_json_or_yaml

from .config import PluginConfig


def get_config_path(filename: str = "configuration.yaml") -> Optional[Path]:
    """Attempts to find a config file given a filename."""
    for path in _try_get_config(filename):
        if path.exists():
            return path
    return None


def _try_get_config(filename: str) -> Iterator[Path]:
    """Attempts to find a filename in common INGInious directories."""
    dirs = [".", "/", "/var/www/INGInious", "/var/www"]
    for d in dirs:
        yield Path(d) / filename


def update_config_file(config_path: Path, plugin_config: PluginConfig) -> None:
    p = str(config_path.absolute())
    config = load_json_or_yaml(p)
    try:
        for plugin in config["plugins"]:
            if plugin["plugin_module"] == "inginious_coding_style":
                plugin = plugin_config.dict()  # overwrite in-place
                break
    except KeyError as e:
        raise  # TODO: add proper exception handling

    # Create backup of config before overwriting
    shutil.copy(p, f"{p}.bak")
    write_json_or_yaml(p, config)
