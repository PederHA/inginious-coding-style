from datetime import datetime
from inginious.frontend.courses import Course
from inginious.frontend.tasks import Task

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from inginious_coding_style.config import PluginConfig
from inginious_coding_style.grades import get_grades
from inginious_coding_style.submission import Submission, get_submission
from unittest.mock import Mock


@pytest.mark.parametrize(
    "submission",
    [
        pytest.lazy_fixture("submission_nogrades"),
        pytest.lazy_fixture("submission_grades"),
    ],
)
def test_get_submission(submission, course, task):
    """Tests validation of a submission with and without grades."""
    # FIXME: this test will not catch if a value is OMITTED after parsing
    # we should iterate through the original submission instead of the parsed submission
    s = get_submission(submission, course, task)
    for attr_name, attr_value in s:
        if attr_name == "custom":
            assert attr_value.coding_style_grades == get_grades(
                submission[attr_name].get("coding_style_grades", {})
            )
        # Skip these two attributes
        # TODO: FIX FIXTURES
        elif attr_name in ["course", "task"]:
            continue
        else:
            assert submission[attr_name] == attr_value


@given(
    courseid=st.text(),
    taskid=st.text(),
    status=st.text(),
    submitted_on=st.datetimes(),
    username=st.lists(st.text()),
)
@pytest.mark.parametrize(
    "submission",
    [
        pytest.lazy_fixture("submission_nogrades"),
        pytest.lazy_fixture("submission_grades"),
    ],
)
def test_get_submission_same_as_constructor(
    submission,
    courseid,
    taskid,
    status,
    submitted_on,
    username,
    course,
    task,
):
    """Tests that `get_submission()` returns the same as unpacking kwargs to
    `Submission`'s constructor."""
    submission["courseid"] = courseid
    submission["taskid"] = taskid
    submission["status"] = status
    submission["submitted_on"] = submitted_on
    submission["username"] = username
    assert Submission(**submission, course=course, task=task) == get_submission(
        submission, course, task
    )


def test_group_submission(submission_grades, course, task):
    submission_grades["username"] = ["user_one", "user_two"]
    submission = get_submission(submission_grades, course, task)
    assert submission.is_group_submission
    assert len(submission.username) == 2


def test_mangled_submission(submission_nogrades, course, task):
    # TODO: make submission fixtures function scoped
    # while not breaking hypothesis tests. Context manager?
    for k in [
        "_id",
        "response_type",
        "input",
        "archive",
        "custom",
        "problems",
        "result",
        "state",
        "stderr",
        "stdout",
        "text",
        "user_ip",
    ]:
        # The absense of these keys should not make the submission fail to validate
        submission_nogrades.pop(k)
        assert get_submission(
            submission_nogrades, course, task
        ), f"Absence of {k} causes validation error"


def test_get_weighted_mean(
    submission_pydantic_grades: Submission, config_pydantic_full: PluginConfig
):
    sub = submission_pydantic_grades
    conf = config_pydantic_full

    sub.grade = 100.0
    conf.weighted_mean.weighting = 0.25

    # Set all grades to 100
    sub.custom.coding_style_grades["comments"].grade = 100
    sub.custom.coding_style_grades["modularity"].grade = 100
    sub.custom.coding_style_grades["structure"].grade = 100
    sub.custom.coding_style_grades["idiomaticity"].grade = 100

    assert sub.get_weighted_mean(conf) == 100.0

    sub.custom.coding_style_grades["comments"].grade = 0
    assert sub.get_weighted_mean(conf) == 93.75

    # Set weighting to 0
    conf.weighted_mean.weighting = 0.0
    assert sub.get_weighted_mean(conf) == 100.0

    # 0 * 1 + 100 * 0 = 0
    sub.custom.coding_style_grades["comments"].grade = 100
    sub.grade = 0.0
    assert sub.get_weighted_mean(conf) == 0.0


# FIXME: I am terrible at hypothesis.
# How to do this without disabling health check?
@given(
    submission_grade=st.floats(0.0, 100.0),
    weighting=st.floats(0.0, 1.0),
    comments_grade=st.floats(0.0, 100.0),
    modularity_grade=st.floats(0.0, 100.0),
    structure_grade=st.floats(0.0, 100.0),
    idiomaticity_grade=st.floats(0.0, 100.0),
)
@settings(suppress_health_check=HealthCheck.all())  # sorry
def test_get_weighted_mean_fuzz(
    submission_pydantic_grades: Submission,
    config_pydantic_full: PluginConfig,
    submission_grade,
    weighting,
    comments_grade,
    modularity_grade,
    structure_grade,
    idiomaticity_grade,
):
    sub = submission_pydantic_grades
    conf = config_pydantic_full

    sub.grade = submission_grade
    conf.weighted_mean.weighting = weighting

    sub.custom.coding_style_grades["comments"].grade = comments_grade
    sub.custom.coding_style_grades["modularity"].grade = modularity_grade
    sub.custom.coding_style_grades["structure"].grade = structure_grade
    sub.custom.coding_style_grades["idiomaticity"].grade = idiomaticity_grade

    mean_style = sub.custom.coding_style_grades.get_mean(conf)
    style_grade_coeff = conf.weighted_mean.weighting
    base_grade_coeff = 1 - style_grade_coeff
    weighted_mean = (sub.grade * base_grade_coeff) + (mean_style * style_grade_coeff)

    assert pytest.approx(sub.get_weighted_mean(conf), weighted_mean)


@pytest.mark.parametrize(
    "submission",
    [
        pytest.lazy_fixture("submission_nogrades"),
        pytest.lazy_fixture("submission_grades"),
    ],
)
def test_get_submission_timestamp(submission, course, task):
    s = get_submission(submission, course, task)
    s.submitted_on = datetime(year=2021, month=8, day=4, hour=12, minute=0, second=0)
    assert s.get_timestamp() == "2021-08-04 12:00:00"


def test_get_submission_timestamp_unknown(submission_grades, course, task):
    # The submitted_on attribute should never be None, but we test
    # its behavior regardless
    s = get_submission(submission_grades, course, task)
    s.submitted_on = None
    assert s.get_timestamp() == "Unknown"


class MockSubmission(Submission):
    course = Mock(spec=Course)
    task = Mock(spec=Task)


@given(st.builds(MockSubmission))
def test_submission_fuzz(sub: Submission):
    assert 0 <= sub.grade <= 100
    assert len(sub.username) != 0
    assert sub.submitted_on is not None
    assert datetime.now() > sub.submitted_on
    assert sub.custom.coding_style_grades is not None

    # Test serialization
    s = sub.dict()
    assert "course" not in s
    assert "task" not in s
    assert get_submission(s, sub.course, sub.task) == sub
