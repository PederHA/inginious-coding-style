from common import dump_yaml

from inginious_coding_style.config import PluginConfigIn

schema = PluginConfigIn.schema()

dump_yaml("schema.yml", schema)
