from typing import Any, List
from pydantic import BaseModel, validator
from pydantic.fields import ModelField
from .logger import get_logger
from .grades import CodingStyleGrade

_categories = list(CodingStyleGrade.schema()["properties"].keys())


class PluginConfig(BaseModel):
    name: str = "INGInious Coding Style"
    enabled: List[str] = _categories

    @validator("enabled", pre=True)
    def validate_enabled_pre(cls, enabled: Any, field: ModelField) -> Any:
        """Handles empty input without having to declare enabled as Optional[]"""
        if enabled is None:
            return []
        return enabled

    @validator("enabled")
    def validate_enabled(cls, enabled: List[str], field: ModelField) -> List[str]:
        """Validates values in list of enabled categories."""
        for val in list(enabled):
            if val not in _categories:
                enabled.remove(val)
        if not enabled:
            logger = get_logger()
            logger.warning(
                "INGInious Coding Style: No valid values received for option 'enabled'. "
                f"Falling back on defaults: {_categories}"
            )
            enabled = _categories
        return enabled
