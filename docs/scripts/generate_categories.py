from pathlib import Path
import sys
from yaml import load, dump
from yaml import Dumper


SCRIPT_PATH = Path(__file__).parent.absolute()
DATA_DIR = SCRIPT_PATH.parent / "data"
PLUGIN_DIR = SCRIPT_PATH.parent.parent / "inginious_coding_style"
sys.path.append(str(PLUGIN_DIR))

from inginious_coding_style.grades import DEFAULT_CATEGORIES


class FixedIndentDumper(Dumper):
    def increase_indent(self, flow=False, *args, **kwargs):
        return super().increase_indent(flow=flow, indentless=False)


with open(DATA_DIR / "categories.yml", "w", encoding="utf-8") as f:
    dicts = [c.dict() for c in DEFAULT_CATEGORIES.values()]
    categories = [
        {"id": d["id"], "name": d["name"], "description": d["description"]}
        for d in dicts
    ]
    f.write(
        dump(
            {"categories": categories},
            indent=2,
            default_flow_style=False,
            sort_keys=False,
            Dumper=FixedIndentDumper,
        )
    )
