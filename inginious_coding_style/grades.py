from __future__ import annotations

from typing import Set, TYPE_CHECKING

if TYPE_CHECKING:
    from .config import PluginConfig

from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field, validator

from ._types import GradesIn


class BaseGrade(BaseModel):
    """Represents a grade given to a submission."""

    # NOTE: All attributes NEED default values
    id: str
    grade: int = Field(ge=0, le=100, default=100)
    feedback: str = Field("", max_length=5000)  # prevent unbounded text input


class GradingCategory(BaseGrade):
    """Represents grading category (including grade and feedback)."""

    id: str  # Key data is stored under
    name: str
    description: str

    @validator("name", pre=True)
    def handle_missing_name(cls, value: Optional[str], values: Dict[str, str]) -> str:
        """Defaults name to `GradingCategory.id.title()` if its value is None."""
        if value is None:
            return values["id"].title()
        return value


class CommentsGrade(GradingCategory):
    id: str = "comments"
    name: str = "Comments"
    description: str = "Use of comments."


class ModularityGrade(GradingCategory):
    id: str = "modularity"
    name: str = "Modularity"
    description: str = (
        "Modularity of the code, i.e. appropriate use of functions and encapsulation."
    )


class StructureGrade(GradingCategory):
    id: str = "structure"
    name: str = "Structure"
    description: str = "The quality of the code's structure, i.e. comprehensible variable names, nesting, and program flow (????)."


class IdiomaticityGrade(GradingCategory):
    id: str = "idiomaticity"
    name: str = "Idiomaticiy"
    description: str = "How idiomatic the code is, i.e. appropriate use of language-specific constructs (list comprehensions, enumerate(), etc. for Python)."


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


def get_grades(grades: GradesIn) -> CodingStyleGrade:
    """Attempts to create a CodingStyleGrade object based on grade data."""
    # This function lets us change the CodingStyleGrade constructor
    # however we want without having to worry about breaking construction
    # of CodingStyleGrade objects elsewhere in the plugin.
    return CodingStyleGrade.parse_obj(grades)


class CodingStyleGrade(BaseModel):
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
                if grade.id == other.id:
                    return True
        return False

    @property
    def grades(self) -> Dict[str, GradingCategory]:
        # TODO: only return enabled grades
        return self.__root__

    def add_category(self, category: GradingCategory) -> None:
        self.__root__[category.id] = category

    def get_average(self, config: PluginConfig) -> float:
        """Returns average grade.

        NOTE: Rounds floating point number to 2 decimal places.
        Don't store this number anywhere!
        """
        grades = [v for (k, v) in self.__root__.items() if k in config.enabled]
        n = len(grades) or 1  # avoid divison by 0
        return round((sum(g.grade for g in grades) / n), 2)

    def _get_include(self) -> Dict[str, Set[str]]:
        return {
            "grades": {
                # Only include attributes defined in BaseGrade
                g: BaseGrade.schema()["properties"].keys()
                for g in self.grades.keys()
            }
        }

    def dump_dict(self) -> Dict[str, BaseGrade]:
        """Returns a dict version of itself that only contains grade and feedback data."""
        return self.dict(exclude_none=True, include=self._get_include())

    def dump_json(self) -> str:
        """Returns JSON-serialized string of itself with None fields excluded."""
        return self.json(exclude_none=True, include=self._get_include())
