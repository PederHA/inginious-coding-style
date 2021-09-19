"""Module for filesystem functions."""

import shutil
from pathlib import Path
from typing import Optional

from inginious.common.base import load_json_or_yaml, write_json_or_yaml

from .config import PluginConfig


def get_config_path(filename: str = "configuration.yaml") -> Optional[Path]:
    """Attempts to find a config file given a filename."""
    for d in [".", "/", "/var/www/INGInious", "/var/www"]:
        path = Path(d) / filename
        if path.exists():
            return path
    return None


def update_config_file(plugin_config: PluginConfig, config_path: Path) -> None:
    """Updates the INGInious configuration with new config values.

    Parameters
    ----------
    config_path : Path
        Path to INGInious configuration file
    plugin_config : PluginConfig
        The updated configuration

    Raises
    ------
    `Exception`
        Raised if plugin configuration block cannot be found in `config["plugins"]`
    """
    p = str(config_path.absolute())
    config = load_json_or_yaml(p)
    try:
        plugin = next(
            c
            for c in config["plugins"]
            if c["plugin_module"] == "inginious_coding_style"
        )
        plugin_idx = config["plugins"].index(plugin)
    except (StopIteration, ValueError) as e:
        raise Exception(
            f"Unable to find Coding Style plugin configuration in {config_path}."
        )

    # Add new and updated categories
    # TODO: refactor. This is a mess that is waiting to create technical debt.
    plugin["categories"] = [
        category.dict(include={"id", "name", "description"})
        for category in plugin_config.enabled.values()
    ]
    plugin["enabled"] = [c["id"] for c in plugin["categories"]]

    plugin["weighted_mean"]["weighting"] = plugin_config.weighted_mean.weighting
    plugin["weighted_mean"]["enabled"] = plugin_config.weighted_mean.enabled
    plugin["task_list_bars"] = plugin_config.task_list_bars.dict()
    plugin["show_graders"] = plugin_config.show_graders
    plugin["submission_query"] = plugin_config.submission_query.dict()

    config["plugins"][plugin_idx] = plugin

    # Create backup of config before overwriting
    shutil.copy(p, f"{p}.bak")
    write_json_or_yaml(p, config)
