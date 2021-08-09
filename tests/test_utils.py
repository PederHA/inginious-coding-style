import pytest
from inginious_coding_style.utils import (
    has_coding_style_grades,
)

from hypothesis import given, strategies as st


@pytest.mark.skip("Needs a proper strategy for custom dict")
@given(
    custom=st.dictionaries(
        st.text(), st.one_of(st.text(), st.lists(st.text()), st.none())
    )
)
def test_has_coding_style_grades_fuzz(submission_nogrades, custom):
    submission_nogrades["custom"] = custom
    assert not has_coding_style_grades(submission_nogrades)


def test_has_coding_style_grades(submission_nogrades, submission_grades):
    assert not has_coding_style_grades(submission_nogrades)
    assert has_coding_style_grades(submission_grades)
    s = {"custom": {"coding_style_grades": {}}}
    assert not has_coding_style_grades(s)
