from logging import Logger
from typing import Any, Dict, Union, OrderedDict, Protocol
from inginious.frontend.user_manager import UserManager

# An INGInious submission
Submission = OrderedDict[str, Any]

# Grades from a single category
GradingCategoryIn = Dict[str, Union[str, int]]

# Mapping of coding style grades
GradesIn = Dict[str, GradingCategoryIn]


class INGIniousPageProto(Protocol):
    _logger: Logger

    @property
    def user_manager(self) -> UserManager:
        ...
