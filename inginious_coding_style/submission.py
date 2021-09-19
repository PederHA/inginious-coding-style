from datetime import datetime
from typing import Any, List, Optional, OrderedDict, Union

from bson import ObjectId
from inginious.frontend.courses import Course
from inginious.frontend.tasks import Task
from pydantic import BaseModel, Field, ValidationError, validator

from ._types import GradesIn, INGIniousSubmission
from .config import PluginConfig
from .grades import CodingStyleGrades, get_grades
from .logger import get_logger


class Custom(BaseModel):
    """Represents the contents of an INGInious submission's `"custom"` key."""

    coding_style_grades: CodingStyleGrades = Field(default_factory=CodingStyleGrades)
    graded_by: List[str] = []

    class Config:
        # We don't care about other custom entries but we can't discard them
        # because they might contain data from other plugins that we have to include
        # when serializing the object (to store in the database).
        extra = "allow"

    @validator("coding_style_grades", pre=True)
    def get_style_grades(
        cls, grades: Union[CodingStyleGrades, GradesIn]
    ) -> Optional[CodingStyleGrades]:
        """Attempts to parse `grades` as a `CodingStylesGrade`.
        Falls back on `None` if grades cannot be validated."""
        if isinstance(grades, CodingStyleGrades):
            return grades
        try:
            return get_grades(grades)
        except ValidationError:
            if grades:
                # FIXME: Find out if this log is actually helpful
                get_logger().error(f"Failed to validate grades: {grades}")
        return None


class Submission(BaseModel):
    """Represents an INGInious submission."""

    # Attributes are defined based on the following:
    # https://docs.inginious.org/en/v0.7/dev_doc/internals_doc/submissions.html#state
    # Attributes annotated with `Any` give us IDE auto-completion without
    # the model doing any sort of validation of the values.

    _id: ObjectId
    courseid: str
    taskid: str
    status: Any
    submitted_on: datetime = Field(default_factory=datetime.now)
    username: List[str]
    response_type: Any
    input: Any
    archive: Any
    custom: Custom = Field(default_factory=Custom)
    grade: float = Field(ge=0.0, le=100.0)
    problems: Any
    result: Any
    state: Any
    stderr: Any
    stdout: Any
    text: Any

    class Config:
        arbitrary_types_allowed = True  # support ObjectId
        extra = "allow"  # we don't validate the other dict keys

    @property
    def coding_style_grades(self) -> CodingStyleGrades:
        return self.custom.coding_style_grades

    @validator("custom", pre=True)
    def check_custom_key(cls, custom: Any) -> Union[dict, Custom]:
        """Makes sure that the value for `custom` is either an instance
        of `Custom` or a dict.

        If the value is not a dict, it is inserted into a new dict under the key `"original"`
        """
        if isinstance(custom, Custom):
            return custom
        if not isinstance(custom, dict):
            # Put original contents into a dict under key "original"
            custom = {"original": custom}
        return custom

    @validator("username")
    def check_empty_username(cls, username: List[str]) -> List[str]:
        if len(username) == 0:
            return ["Missing user"]
        return username

    @property
    def is_group_submission(self) -> bool:
        return len(self.username) > 1

    def get_timestamp(self) -> str:
        s = self.submitted_on
        return s.strftime("%Y-%m-%d %H:%M:%S") if s else "Unknown"

    def get_weighted_mean(self, config: PluginConfig) -> float:
        base_grade = self.grade
        style_grades = self.custom.coding_style_grades
        if not style_grades:
            return base_grade
        style_mean = style_grades.get_mean(config, round_grade=False)

        # Calculate weighting
        style_grade_coeff = config.weighted_mean.weighting
        base_grade_coeff = 1 - style_grade_coeff

        mean = (base_grade * base_grade_coeff) + (style_mean * style_grade_coeff)
        if not config.weighted_mean.round:
            return mean
        return round(mean, config.weighted_mean.round_digits)

    def delete_coding_style_grades(self) -> None:
        """Deletes ALL coding style grades from a submission."""
        self.custom.coding_style_grades.delete_grades()


def get_submission(submission: INGIniousSubmission) -> Submission:
    """Validates a submission returned by
    `INGIniousAuthPage.submission_manager.get_submission()`.

    Returns `Submission`
    """
    try:
        sub = Submission(**submission)
    except ValidationError:
        get_logger().exception(f"Failed to validate submission {submission['_id']}")
        raise
    return sub
