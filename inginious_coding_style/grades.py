from typing import Dict, Optional, Union
from pydantic import BaseModel, Field, ValidationError

GradesIn = Dict[str, Dict[str, Union[str, int]]]


class Grade(BaseModel):
    # NOTE: All attributes NEED default values
    grade: int = Field(ge=0, le=100, default=100)
    feedback: Optional[str] = None


class CodingStyleGrade(BaseModel):
    comments: Optional[Grade] = None
    structure: Optional[Grade] = None
    modularity: Optional[Grade] = None
    idiomaticity: Optional[Grade] = None

    class Config:
        extra = "allow"  # TODO: find out of this is desired

    @property
    def average(self) -> float:
        # Dynamically get grades to accomodate adding/removing grading categories
        # grades = [g for g in self.__dict__.values() if isinstance(g, Grade)]
        grades = self.get_grades()
        n = len(grades) or 1  # avoid divison by 0
        return sum(g.grade for g in grades.values()) / n

    def get_grades(self) -> Dict[str, Grade]:
        """Retrieves all defined grades (i.e. not None)."""
        return {name: g for (name, g) in self.__dict__.items() if isinstance(g, Grade)}

    def dump_dict(self) -> Dict[str, Grade]:
        """Returns a dict version of itself with None fields excluded."""
        return self.dict(exclude_none=True)

    def dump_json(self) -> str:
        """Returns JSON-serialized string with None fields excluded."""
        return self.json(exclude_none=True)


############################################################
# This is NOT ideal!
############################################################


def get_grade(grades: GradesIn) -> CodingStyleGrade:
    try:
        c = CodingStyleGrade(**grades)
    except ValidationError as e:
        grades = _handle_validation_error(grades, e)
        return get_grade(
            grades
        )  # could hit recursion limit if this is isn't robust (which it isn't)
    return c


def _handle_validation_error(grades: GradesIn, error: ValidationError) -> GradesIn:
    """Simple pydantic ValidationError handling. Removes invalid values."""
    for err in error.errors():
        # Primitive way to handle this error rn
        l = err.get("loc")
        if not l:
            raise error
        attr_name = l[0]
        l = l[0:]
        for key in (Grade.schema())["properties"]:
            if key in l:
                grades[attr_name].pop(key)
    return grades
