from inginious_coding_style.grades import get_grades, CodingStyleGrades
from hypothesis import given, strategies as st
import pytest
from pydantic import ValidationError


def test_get_grades(grades):
    assert get_grades(grades) == CodingStyleGrades(__root__=grades)
    assert get_grades(grades) == CodingStyleGrades.parse_obj(grades)
    g = get_grades(grades)
    for category in grades:
        g.grades[category] == grades[category]


# How to avoid having to wrap the tests in classes
# when using fixtures together with hypothesis?
class TestGrades:
    @given(grade=st.integers())
    def test_grades_fuzz(self, grade, grades):
        grades["comments"]["grade"] = grade
        if grade < 0 or grade > 100:
            with pytest.raises(ValidationError):
                get_grades(grades)
        else:
            g = get_grades(grades)
            assert g.grades["comments"].grade == grade


class TestFeedback:
    @given(feedback=st.text())
    def test_feedback_fuzz(self, feedback, grades):
        grades["comments"]["feedback"] = feedback
        get_grades(grades)
