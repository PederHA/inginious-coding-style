from typing import Any, Dict, List, Optional
from pydantic import BaseModel, validator, Field
from pydantic.fields import ModelField
from .logger import get_logger
from .grades import GradingCategory, DEFAULT_CATEGORIES


def none_returns_defaults(value: Any, field: ModelField) -> Any:
    """Custom validator that attempts to call the field's default factory
    or returns the field's default value if `None` is passed in.

    Handles cases where the contents of a config section is deleted, but
    its header remains.

    If the field does not have defaults, we let Pydantic handle the
    resulting validation error.

    Example:
    ------

    We go from this:
    ```yml
    enabled:
        - comments
        - modularity
        - structure
        - idiomaticity
    ```

    To this:
    ```yml
    enabled:
    ```

    In this case, the value of `enabled` is interpreted as `None` by
    the INGInious YAML parser. When that happens, this function serves
    as a failsafe, so that the field's defaults kick in.
    """
    if value is None:
        if field.default is not None:
            return field.default
        elif field.default_factory is not None:
            return field.default_factory()
    return value


class SubmissionQuerySettings(BaseModel):
    header: str = "csg"
    priority: int = 3000  # can you do negative numbers?
    button: bool = True


class WeightedMeanSettings(BaseModel):
    enabled: bool = False
    weighting: float = Field(ge=0.00, le=1.00, default=0.25)
    task_list_bar: bool = True


class PluginConfigIn(BaseModel):
    """Maps to the plugin configuration options found in configuration.yaml"""

    # Name of plugin
    name: str = "INGInious Coding Style"

    # Enabled grading categories
    enabled: List[str] = Field(list(DEFAULT_CATEGORIES.keys()))

    # Custom grading categories
    categories: List[GradingCategory] = Field([])

    # Submission query page settings
    submission_query: SubmissionQuerySettings = Field(
        default_factory=SubmissionQuerySettings
    )

    # Weighted mean grades settings
    weighted_mean: WeightedMeanSettings = Field(default_factory=WeightedMeanSettings)

    # validators
    # Reusing validators: https://pydantic-docs.helpmanual.io/usage/validators/#reuse-validators
    # "*" validator: https://pydantic-docs.helpmanual.io/usage/validators/#pre-and-per-item-validators
    handle_none = validator("*", allow_reuse=True, pre=True)(none_returns_defaults)


# TODO: Merge PluginConfigIn and PluginConfig


class PluginConfig(BaseModel):
    """The config used by the plugin.

    This class consolidates the fields `enabled` and `categories` from the input config.
    Furthermore, it retrieves the corresponding `GradingCategory` for any enabled
    predfined categories.
    """

    name: str
    enabled: Dict[str, GradingCategory] = {}
    submission_query: SubmissionQuerySettings
    weighted_mean: WeightedMeanSettings

    def __init__(self, config_in: PluginConfigIn) -> None:
        enabled = self._make_dict_from_enabled(
            enabled=config_in.enabled,
            custom_categories={c.id: c for c in config_in.categories},
        )
        super().__init__(
            name=config_in.name,
            enabled=enabled,
            weighted_mean=config_in.weighted_mean,
            submission_query=config_in.submission_query,
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
