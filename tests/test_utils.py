from datetime import datetime

import pytest
from inginious_coding_style.submission import get_submission
from inginious_coding_style.utils import get_submission_timestamp


@pytest.mark.parametrize(
    "submission",
    [
        pytest.lazy_fixture("submission_nogrades"),
        pytest.lazy_fixture("submission_grades"),
    ],
)
def test_get_submission_timestamp(submission):
    s = get_submission(submission)
    s.submitted_on = datetime(year=2021, month=8, day=4, hour=12, minute=0, second=0)
    assert get_submission_timestamp(s) == "2021-08-04 12:00:00"


def test_get_submission_timestamp_unknown(submission_grades):
    # The submitted_on attribute should never be None, but we test
    # its behavior regardless
    s = get_submission(submission_grades)
    s.submitted_on = None
    assert get_submission_timestamp(s) == "Unknown"
