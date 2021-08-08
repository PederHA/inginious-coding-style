from __future__ import annotations

from typing import Dict, Optional, Union, TYPE_CHECKING

from pydantic import BaseModel, Field, validator

from ._types import GradesIn

if TYPE_CHECKING:
    from .config import PluginConfig


class GradingCategory(BaseModel):
    """Represents a grading category."""

    id: str  # Key data is stored under
    name: str
    description: str
    grade: int = Field(default=100, ge=0, le=100)
    feedback: str = Field(default="", max_length=5000)  # prevent unbounded text input

    @validator("name", pre=True)
    def handle_missing_name(cls, value: Optional[str], values: Dict[str, str]) -> str:
        """Defaults name to `GradingCategory.id.title()` if its value is None."""
        if value is None:
            return values["id"].title()
        return value


class CodingStyleGrades(BaseModel):
    # https://pydantic-docs.helpmanual.io/usage/models/#custom-root-types
    __root__: Dict[str, GradingCategory] = {}

    def __bool__(self) -> bool:
        """Evaluates to true if at least one grade is defined."""
        return any(g for g in self.grades)

    def __contains__(self, other: Union[str, GradingCategory]) -> bool:
        if isinstance(other, str):
            return other in self.__root__
        elif isinstance(other, GradingCategory):
            for grade in self.__root__.values():
                if grade.id == other.id:  # We assume identical ID means they are equal
                    return True
        return False

    def __getitem__(self, key: str) -> GradingCategory:
        return self.__root__[key]

    @property
    def grades(self) -> Dict[str, GradingCategory]:
        return self.__root__

    def add_category(self, category: GradingCategory) -> None:
        """Adds a grading category

        Parameters
        ----------
        category : `GradingCategory`
            The grading category to add.
        """
        self.__root__[category.id] = category

    def remove_category(
        self, category: Union[str, GradingCategory]
    ) -> Optional[GradingCategory]:
        """Removes a grading category.

        Parameters
        ----------
        category : Union[str, GradingCategory]
            Name of category or a `GradingCategory` object.
        """
        if isinstance(category, str):
            return self.__root__.pop(category, None)
        elif isinstance(category, GradingCategory):
            return self.__root__.pop(category.id, None)
        # TODO: raise exception if invalid category?
        raise TypeError(
            "Argument 'category' must be of type 'str' or 'GradingCategory'."
        )

    def get_mean(
        self,
        config: Optional[PluginConfig] = None,
        round_grade: bool = True,
        ndigits: int = 2,
    ) -> float:
        """Returns mean coding style grade.
        Optionally calculate only based on enabled grading categories.

        Parameters
        ----------
        config : `Optional[PluginConfig]`, optional
            Plugin config specifying enabled categories, by default None
        round_grade : `bool`, optional
            Whether or not to round the mean grade value, by default True
        ndigits : `int`, optional
            Rounding precision, by default 2 digits after decimal point

        Returns
        -------
        `float`
            Mean grade
        """
        if config is not None:
            grades = [v for (k, v) in self.__root__.items() if k in config.enabled]
        else:
            grades = [v for (k, v) in self.__root__.items()]
        n = len(grades) or 1  # avoid division by 0
        avg = sum(g.grade for g in grades) / n
        if round_grade:
            return round(avg, ndigits)
        return avg

    def dict(self, *args, **kwargs) -> Dict[str, GradingCategory]:  # type: ignore
        """Returns a dict version of its own `__root__` attribute."""
        return super().dict()["__root__"]


def get_grades(
    grades: Union[GradesIn, Dict[str, GradingCategory]]
) -> CodingStyleGrades:
    """Attempts to create a CodingStyleGrades object based on grade data."""
    # This function lets us change the CodingStyleGrades constructor
    # however we want without having to worry about breaking construction
    # of CodingStyleGrades objects elsewhere in the plugin, if this is the
    # canonical way to create CodingStyleGrades objects.
    return CodingStyleGrades.parse_obj(grades)


def add_config_categories(
    grades: CodingStyleGrades, config: PluginConfig
) -> CodingStyleGrades:
    """Makes sure all enabled categories are added to a `CodingStyleGrades` object."""
    for category_id, category in config.enabled.items():
        if category_id not in grades:
            grades.add_category(category)
    return grades


DEFAULT_CATEGORIES = {
    "comments": GradingCategory(
        id="comments",
        name="Comments",
        description="Appropriate use of comments.",
    ),
    "modularity": GradingCategory(
        id="modularity",
        name="Modularity",
        description="Modularity of the code, i.e. appropriate use of functions and encapsulation.",
    ),
    "structure": GradingCategory(
        id="structure",
        name="Structure",
        description="The quality of the code's structure, i.e. comprehensible variable names, nesting, and program flow.",
    ),
    "idiomaticity": GradingCategory(
        id="idiomaticity",
        name="Idiomaticity",
        description="How idiomatic the code is, i.e. appropriate use of language-specific constructs (list comprehensions, enumerate(), etc. for Python).",
    ),
}
