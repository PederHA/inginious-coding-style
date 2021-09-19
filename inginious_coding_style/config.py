from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator
from pydantic.fields import ModelField

from .grades import DEFAULT_CATEGORIES, GradingCategory
from .logger import get_logger


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
    as a failsafe, so that the field's defaults kick in instead of leading
    to a validation error because of an unexpected None value.
    """
    if value is None:
        if field.default is not None:
            return field.default
        elif field.default_factory is not None:
            return field.default_factory()
    return value


class SubmissionQuerySettings(BaseModel):
    header: str = "CSG"
    priority: int = 3000  # can you do negative numbers?
    button: bool = True


class WeightedMeanSettings(BaseModel):
    enabled: bool = False
    weighting: float = Field(ge=0.00, le=1.00, default=0.25)
    round: bool = True
    round_digits: int = Field(ge=0, default=2)


class BarBase(BaseModel):
    enabled: bool = True
    label: str


class TotalGradeBar(BarBase):
    label: str = "Grade"


class BaseGradeBar(BarBase):
    label: str = "Completion"


class StyleGradeBar(BarBase):
    label: str = "Coding Style"


class TaskListBars(BaseModel):
    total_grade: TotalGradeBar = Field(default_factory=TotalGradeBar)
    base_grade: BaseGradeBar = Field(default_factory=BaseGradeBar)
    style_grade: StyleGradeBar = Field(default_factory=StyleGradeBar)


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

    # Settings for bars displayed on the task list page
    task_list_bars: TaskListBars = Field(default_factory=TaskListBars)

    # Show/hide "graded by" on student coding style grades page.
    show_graders: bool = False

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
    task_list_bars: TaskListBars
    show_graders: bool

    class Config:
        extras = "ignore"

    def __init__(self, config_in: PluginConfigIn) -> None:
        # Merge the two attributes "enabled" and "categories"
        config_in.enabled = self._make_dict_from_enabled(
            enabled=config_in.enabled,
            custom_categories={c.id: c for c in config_in.categories},
        )
        super().__init__(**(config_in.dict()))

    # TODO: REFACTOR.
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
