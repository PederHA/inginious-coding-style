import pytest
from hypothesis import given
from hypothesis import strategies as st
from werkzeug.datastructures import ImmutableMultiDict

from inginious_coding_style.utils import (has_coding_style_grades,
                                          parse_form_data)


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


def test_parse_form_data():
    form_data = ImmutableMultiDict(
        [
            ("comments_grade", "11"),
            ("comments_feedback", "Bad!"),
            ("modularity_grade", "22"),
            ("modularity_feedback", "Ok."),
            ("structure_grade", "33"),
            ("structure_feedback", "Better."),
            ("idiomaticity_grade", "44"),
            ("idiomaticity_feedback", "Good!"),
        ]
    )
    form = parse_form_data(form_data)
    assert form["comments"]["grade"] == "11"
    assert form["comments"]["feedback"] == "Bad!"
    assert form["modularity"]["grade"] == "22"
    assert form["modularity"]["feedback"] == "Ok."
    assert form["structure"]["grade"] == "33"
    assert form["structure"]["feedback"] == "Better."
    assert form["idiomaticity"]["grade"] == "44"
    assert form["idiomaticity"]["feedback"] == "Good!"
