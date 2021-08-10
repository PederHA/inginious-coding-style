import copy
from datetime import datetime
from unittest.mock import Mock

import pytest
from bson import ObjectId
from inginious.frontend.courses import Course
from inginious.frontend.tasks import Task
from inginious_coding_style.config import get_config
from inginious_coding_style.grades import get_grades
from inginious_coding_style.submission import get_submission


# TODO: fix scope / use generator fixture / create context manager
@pytest.fixture(scope="class")
def grades():
    yield {
        "comments": {
            "id": "comments",
            "name": "Comments",
            "description": "Appropriate use of comments.",
            "grade": 10,
            "feedback": "aaa",
        },
        "modularity": {
            "id": "modularity",
            "name": "Modularity",
            "description": "Modularity of the code, i.e. appropriate use of functions and encapsulation.",
            "grade": 20,
            "feedback": "bbb",
        },
        "structure": {
            "id": "structure",
            "name": "Structure",
            "description": "The quality of the code's structure, i.e. comprehensible variable names, nesting, and program flow.",
            "grade": 30,
            "feedback": "ccc",
        },
        "idiomaticity": {
            "id": "idiomaticity",
            "name": "Idiomaticity",
            "description": "How idiomatic the code is, i.e. appropriate use of language-specific constructs (list comprehensions, enumerate(), etc. for Python).",
            "grade": 40,
            "feedback": "ddd",
        },
    }


@pytest.fixture
def grades_pydantic(grades):
    return get_grades(grades)


@pytest.fixture
def coding_style_grades_dict(grades):
    yield {"coding_style_grades": grades}


@pytest.fixture(scope="function")
def submission_nogrades() -> dict:
    yield {
        "_id": ObjectId("123456789abc123456789abc"),
        "courseid": "mycourse",
        "taskid": "mytask",
        "status": "done",
        "submitted_on": datetime(
            year=2021, month=8, day=4, hour=12, minute=0, second=0
        ),
        "username": ["testuser"],
        "response_type": "rst",
        "input": ObjectId("123456789123456789123456"),
        "archive": None,
        "custom": {},
        "grade": 100.0,
        # FIXME: docs: https://docs.inginious.org/en/v0.7/dev_doc/internals_doc/submissions.html#state
        # what does "problems is a dict of tuple, in the form {'problemid': result}" mean?
        "problems": {},
        "result": "success",
        "state": "",
        "stderr": "",
        "stdout": "",
        "text": "",
        "user_ip": "127.0.0.1",
    }


@pytest.fixture
def submission_grades(submission_nogrades, coding_style_grades_dict):
    sub = copy.deepcopy(submission_nogrades)
    sub["custom"] = coding_style_grades_dict
    yield sub


@pytest.fixture
def submission_pydantic_grades(submission_grades, course, task):
    yield get_submission(submission_grades, course, task)


@pytest.fixture(scope="session")
def course():
    return Mock(spec=Course)


@pytest.fixture(scope="session")
def task():
    return Mock(spec=Task)


@pytest.fixture
def config_raw_minimal():
    """A minimal plugin config.
    Represented as a dict parsed by the INGInious YAML parser.
    """
    yield {
        "plugin_module": "inginious_coding_style",
        "name": "INGInious Coding Style",
    }


@pytest.fixture
def config_raw_full(config_raw_minimal: dict):
    """A plugin config with all options used.
    Represented as a dict parsed by the INGInious YAML parser.
    """
    config_raw_minimal.update(
        {
            "enabled": ["comments", "modularity", "structure", "idiomaticity"],
            "categories": [
                {
                    "id": "custom_category",
                    "name": "Custom Category",
                    "description": "This is a custom category.",
                }
            ],
            "weighted_mean": {"enabled": False, "weighting": 0.25},
            "submission_query": {"header": "CSG", "priority": 3000, "button": True},
        }
    )
    config_raw_minimal["enabled"].append("custom_category")
    yield config_raw_minimal


@pytest.fixture
def config_pydantic_full(config_raw_full):
    yield get_config(config_raw_full)
