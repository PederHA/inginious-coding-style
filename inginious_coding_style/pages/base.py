from pathlib import Path

from inginious.frontend.pages.utils import INGIniousAuthPage

from ..config import PluginConfig
from ..exceptions import init_exception_handlers
from ..logger import get_logger


class BasePluginPage(INGIniousAuthPage):
    _logger = get_logger()

    def __init__(
        self, config: PluginConfig, templates_path: Path, *args, **kwargs
    ) -> None:
        self.config = config
        self.templates_path = templates_path
        self.static_path = templates_path / ".." / "static"
        super().__init__(*args, **kwargs)
        init_exception_handlers(self)
