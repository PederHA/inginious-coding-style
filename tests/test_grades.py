import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from inginious_coding_style.config import PluginConfig
from inginious_coding_style.grades import (CodingStyleGrades, GradingCategory,
                                           add_config_categories, get_grades)


def test_get_grades(grades: dict):
    assert get_grades(grades) == CodingStyleGrades(__root__=grades)
    assert get_grades(grades) == CodingStyleGrades.parse_obj(grades)
    g = get_grades(grades)
    for category in grades:
        g.grades[category] == grades[category]


# How to avoid having to wrap the tests in classes
# when using fixtures together with hypothesis?
class TestGrades:
    @given(grade=st.integers())
    def test_grades_fuzz(self, grade: int, grades: dict):
        grades["comments"]["grade"] = grade
        if grade < 0 or grade > 100:
            with pytest.raises(ValidationError):
                get_grades(grades)
        else:
            g = get_grades(grades)
            assert g.grades["comments"].grade == grade


class TestFeedback:
    @given(feedback=st.text())
    def test_feedback_fuzz(self, feedback: str, grades: dict):
        grades["comments"]["feedback"] = feedback
        get_grades(grades)


def test_remove_category(grades_pydantic: CodingStyleGrades):
    grades_pydantic.remove_category("comments")
    assert "commments" not in grades_pydantic.grades
    category = grades_pydantic["idiomaticity"]
    grades_pydantic.remove_category(category)
    assert "idiomaticity" not in grades_pydantic.grades

    with pytest.raises(TypeError):
        assert grades_pydantic.remove_category(1)  # type: ignore


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


def test_missing_grading_category_name():
    c = {
        "id": "comments",
        "name": None,
        "description": "Appropriate use of comments.",
    }
    category = GradingCategory(**c)
    assert category.name == c["id"].title()
    assert category.name == "Comments"


def test_grades_contains(grades_pydantic: CodingStyleGrades):
    """Tests CodingStyleGrades.__contains__()"""
    for id in ["comments", "modularity", "structure", "idiomaticity"]:
        assert id in grades_pydantic

    for grade in grades_pydantic.grades.values():
        assert grade in grades_pydantic

    # test invalid type
    assert 2 not in grades_pydantic  # type: ignore


def test_add_config_categories(config_pydantic_full: PluginConfig) -> None:
    pre_add_len = len(config_pydantic_full.enabled)
    grades = get_grades(
        {
            "elegance": GradingCategory(
                id="elegance",
                name="Elegance",
                description="Elegance of code",
            )
        }
    )
    categories = add_config_categories(grades, config_pydantic_full)
    assert "elegance" in categories
    assert len(categories) == pre_add_len + 1
