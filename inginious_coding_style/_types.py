from typing import Dict, Union


# Grades from a single category
GradingCategoryIn = Dict[str, Union[str, int]]

# Mapping of coding style grades
GradesIn = Dict[str, GradingCategoryIn]
