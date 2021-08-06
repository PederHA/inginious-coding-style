import pytest

from bson import ObjectId
from datetime import datetime


# TODO: fix scope / use generator fixture / create context manager
@pytest.fixture(scope="class")
def grades() -> dict:
    return {
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
def coding_style_grades_dict(grades):
    return {"coding_style_grades": grades}


@pytest.fixture(scope="module")
def submission_nogrades() -> dict:
    return {
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
def submission_grades(submission_nogrades, coding_style_grades_dict) -> dict:
    submission_nogrades["custom"] = coding_style_grades_dict
    return submission_nogrades


@pytest.fixture
def config_raw_minimal() -> dict:
    """A minimal plugin config as parsed by INGInious."""
    return {
        "plugin_module": "inginious_coding_style",
        "name": "INGInious Coding Style",
    }


@pytest.fixture
def config_raw_full(config_raw_minimal: dict) -> dict:
    """A plugin config with all options used as parsed by INGInious."""
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
            "merge_grades": {"enabled": False, "weighting": 0.50},
            "submission_query": {"header": "CSG", "priority": 3000},
        }
    )
    config_raw_minimal["enabled"].append("custom_category")
    return config_raw_minimal
