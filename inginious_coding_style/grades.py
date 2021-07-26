from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import PluginConfig

from typing import Dict, Optional, Union
from pydantic import BaseModel, Field, validator

from ._types import GradesIn


class Grade(BaseModel):
    grade: int = Field(default=100, ge=0, le=100)
    feedback: str = Field(default="", max_length=5000)  # prevent unbounded text input


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

    @property
    def grades(self) -> Dict[str, GradingCategory]:
        return self.__root__

    # TODO: rename to add_grade?
    def add_category(self, category: GradingCategory) -> None:
        """Adds a grading category

        Parameters
        ----------
        category : `GradingCategory`
            The grading category to add.
        """
        self.__root__[category.id] = category

    def remove_category(self, category: Union[str, GradingCategory]) -> None:
        """Removes a grading category.

        Parameters
        ----------
        category : Union[str, GradingCategory]
            Name of category or a `GradingCategory` object.
        """
        if isinstance(category, str):
            self.__root__.pop(category, None)
        elif isinstance(category, GradingCategory):
            self.__root__.pop(category.id, None)

    def get_mean(
        self, config: PluginConfig, round_grade: bool = True, ndigits: int = 2
    ) -> float:
        """Returns mean of all _enabled_ coding style grades.

        NOTE: Rounds mean grade with 2 digits after decimal point precision by default.
        """
        grades = [v for (k, v) in self.__root__.items() if k in config.enabled]
        n = len(grades) or 1  # avoid divison by 0
        avg = sum(g.grade for g in grades) / n
        if round_grade:
            return round(avg, ndigits)
        return avg

    def dict(self) -> Dict[str, GradingCategory]:  # type: ignore
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


DEFAULT_CATEGORIES = {
    "comments": GradingCategory(
        id="comments",
        name="Comments",
        description="Use of comments.",
    ),
    "modularity": GradingCategory(
        id="modularity",
        name="Modularity",
        description="Modularity of the code, i.e. appropriate use of functions and encapsulation.",
    ),
    "structure": GradingCategory(
        id="structure",
        name="Structure",
        description="The quality of the code's structure, i.e. comprehensible variable names, nesting, and program flow (????).",
    ),
    "idiomaticity": GradingCategory(
        id="idiomaticity",
        name="Idiomaticity",
        description="How idiomatic the code is, i.e. appropriate use of language-specific constructs (list comprehensions, enumerate(), etc. for Python).",
    ),
}
