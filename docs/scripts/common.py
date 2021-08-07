from pathlib import Path
import sys
from typing import Any
from yaml import dump
from yaml import Dumper

# Set up directories
SCRIPT_PATH = Path(__file__).parent.absolute()

# Directory to store category data
DATA_DIR = SCRIPT_PATH.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Lets us import modules from the plugin
PLUGIN_DIR = SCRIPT_PATH.parent.parent
sys.path.append(str(PLUGIN_DIR))

# Custom dumper that matches style used by INGInious config.
class FixedIndentDumper(Dumper):
    def increase_indent(self, flow=False, *args, **kwargs):
        return super().increase_indent(flow=flow, indentless=False)


def dump_yaml(filename: str, obj: Any) -> None:
    if not any(filename.endswith(ext) for ext in [".yaml", ".yml"]):
        filename += ".yml"
    with open(DATA_DIR / filename, "w", encoding="utf-8") as f:
        f.write(
            dump(
                obj,
                indent=2,
                default_flow_style=False,
                sort_keys=False,
                Dumper=FixedIndentDumper,
            )
        )
