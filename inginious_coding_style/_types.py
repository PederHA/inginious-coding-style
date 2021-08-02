from typing import Any, Dict, Union, OrderedDict


# An INGInious submission
Submission = OrderedDict[str, Any]

# Grades from a single category
GradingCategoryIn = Dict[str, Union[str, int]]

# Mapping of coding style grades
GradesIn = Dict[str, GradingCategoryIn]
