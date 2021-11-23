from datetime import datetime
from typing import Any, Dict, List, TypedDict, Union

from bson import ObjectId

# Grades from a single category
GradingCategoryIn = Dict[str, Union[str, int]]

# Mapping of coding style grades
GradesIn = Dict[str, GradingCategoryIn]


class INGIniousSubmission(TypedDict):
    """Represents an INGInious student submission as retrieved by the
    submission manager.

    Source: https://docs.inginious.org/en/v0.7/dev_doc/internals_doc/submissions.html#state
    """

    _id: ObjectId
    courseid: str
    taskid: str
    status: Any
    submitted_on: datetime
    username: List[str]
    response_type: Any
    input: Any
    archive: Any
    custom: dict
    grade: float
    problems: Any
    result: Any
    state: Any
    stderr: Any
    stdout: Any
    text: Any


class INGIniousUserTask(TypedDict):
    """Represents a document from the `user_tasks` DB collection."""

    _id: ObjectId
    courseid: str
    grade: float
    random: list
    state: str
    submissionid: ObjectId
    succeeded: bool
    taskid: str
    tokens: dict
    tried: int
    username: str


class PluginUserTask(INGIniousUserTask):
    """Version of INGIniousUserTask that includes base and mean grades."""

    grade_mean: float
    grade_base: float
