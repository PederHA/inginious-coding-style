from inginious_coding_style.grades import GradingCategory, get_grades, CodingStyleGrades
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


def test_remove_category(grades_pydantic: CodingStyleGrades):
    grades_pydantic.remove_category("comments")
    assert "commments" not in grades_pydantic.grades


def test_delete_grades(grades_pydantic: CodingStyleGrades):
    grades_pydantic.delete_grades()
    assert len(grades_pydantic) == 0


def test_add_category(grades_pydantic: CodingStyleGrades):
    len_pre = len(grades_pydantic)

    in_cat = {
        "id": "mycat",
        "name": "My Category",
        "description": "This is my category.",
    }
    category = GradingCategory(**in_cat)
    grades_pydantic.add_category(category)

    assert grades_pydantic.grades["mycat"].id == "mycat"
    assert grades_pydantic.grades["mycat"].name == "My Category"
    assert grades_pydantic.grades["mycat"].description == "This is my category."
    assert grades_pydantic.grades["mycat"].grade == 100
    assert grades_pydantic.grades["mycat"].feedback == ""

    assert len(grades_pydantic.grades) == len_pre + 1
