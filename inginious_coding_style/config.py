from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, validator, Field
from pydantic.fields import ModelField
from .logger import get_logger
from .grades import GradingCategory, DEFAULT_CATEGORIES


class ExperimentalSettings(BaseModel):
    merge_grades: bool = False
    # automatic_grading: bool = False # NYI (obviously)
    # other experimental settings here...


class PluginConfigIn(BaseModel):
    """Maps to the plugin configuration options found in configuration.yaml"""

    # Name of plugin
    name: str = "INGInious Coding Style"

    # Enabled grading categories
    enabled: List[str] = []

    # Custom grading categories
    categories: List[GradingCategory] = []

    # Experimental settings
    experimental: ExperimentalSettings = Field(default_factory=ExperimentalSettings)

    @validator("enabled", pre=True)
    def accept_enabled_none(cls, enabled: Optional[List[str]]) -> List[str]:
        if enabled is None:
            return []
        return enabled

    @validator("categories", pre=True)
    def accept_categories_none(cls, categories: Optional[List[str]]) -> List[str]:
        if categories is None:
            return []
        return categories

    @validator("experimental", pre=True)
    def accept_experimental_none(
        cls, experimental: Optional[Dict[str, bool]], field: ModelField
    ) -> Union[ExperimentalSettings, Optional[Dict[str, bool]]]:
        if experimental is None and field.default_factory is not None:
            return field.default_factory()
        return experimental


class PluginConfig(BaseModel):
    """The config used by the plugin.

    This class consolidates the fields `enabled` and `categories` from the input config.
    Furthermore, it retrieves the corresponding `GradingCategory` for any enabled
    predfined categories.
    """

    name: str
    enabled: Dict[str, GradingCategory] = {}
    experimental: ExperimentalSettings

    def __init__(self, config_in: PluginConfigIn) -> None:
        enabled = self._make_dict_from_enabled(
            enabled=config_in.enabled,
            custom_categories={c.id: c for c in config_in.categories},
        )
        super().__init__(
            name=config_in.name,
            enabled=enabled,
            experimental=config_in.experimental,
        )

    # TODO: rename method
    def _make_dict_from_enabled(
        self, enabled: List[str], custom_categories: Dict[str, GradingCategory]
    ) -> Dict[str, GradingCategory]:
        """Fetches default categories (if any) and consolidates it with custom categories."""

        if enabled is None:
            enabled = {}

        enabled_categories: Dict[str, GradingCategory] = {}

        # Attempt to get a GradingCategory object for each enabled category
        for cat in enabled:
            # check if a custom category with this name is defined
            category = custom_categories.get(cat)
            if not category:
                # check if category is a default category
                category = DEFAULT_CATEGORIES.get(cat)
                if not category:
                    get_logger().info(
                        f"Ignoring undefined grading category '{cat}' for parameter 'enabled'."
                    )
                    continue
            # Add category
            enabled_categories[cat] = category

        if not enabled_categories:
            get_logger().warning(
                "No valid values received for option 'enabled'. "
                f"Falling back on defaults: {DEFAULT_CATEGORIES.keys()}"
            )
            return DEFAULT_CATEGORIES

        return enabled_categories


def get_config(config: Dict[str, Any]) -> PluginConfig:
    # First we validate the contents of the config file
    conf_in = PluginConfigIn(**config)
    # Then we construct the config used by the plugin
    return PluginConfig(conf_in)
