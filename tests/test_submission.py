import pytest
from inginious_coding_style.grades import get_grades
from inginious_coding_style.submission import Submission, get_submission

from hypothesis import given, strategies as st


@pytest.mark.parametrize(
    "submission",
    [
        pytest.lazy_fixture("submission_nogrades"),
        pytest.lazy_fixture("submission_grades"),
    ],
)
def test_get_submission(submission):
    """Tests validation of a submission with and without grades."""
    # FIXME: this test will not catch if a value is OMITTED after parsing
    # we should iterate through the original submission instead of the parsed submission
    s = get_submission(submission)
    for attr_name, attr_value in s:
        if attr_name == "custom":
            assert attr_value.coding_style_grades == get_grades(
                submission[attr_name].get("coding_style_grades", {})
            )
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
    submission, courseid, taskid, status, submitted_on, username
):
    """Tests that `get_submission()` returns the same as unpacking kwargs to
    `Submission`'s constructor."""
    submission["courseid"] = courseid
    submission["taskid"] = taskid
    submission["status"] = status
    submission["submitted_on"] = submitted_on
    submission["username"] = username
    assert Submission(**submission) == get_submission(submission)


def test_malformed_submission(submission_grades):
    submission_grades["_id"] = None
    submission_grades["problems"] = None
    submission_grades["result"] = None
    assert get_submission(submission_grades)


def test_group_submission(submission_grades):
    submission_grades["username"] = ["user_one", "user_two"]
    submission = get_submission(submission_grades)
    assert submission.is_group_submission
    assert len(submission.username) == 2
