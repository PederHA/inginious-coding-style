from pathlib import Path
from typing import List

import pytest
from pydantic.error_wrappers import ValidationError

from inginious_coding_style.exceptions import (TEMPLATE_FOLDER,
                                               handle_validation_error,
                                               init_exception_handlers,
                                               model_names)
from inginious_coding_style.grades import CodingStyleGrades, GradingCategory
from inginious_coding_style.submission import Submission


def test_template_folder():
    """Tests that new versions of INGInious do not break template fetching logic."""
    assert TEMPLATE_FOLDER.is_dir()

    files = list(TEMPLATE_FOLDER.iterdir())  # type: List[Path]
    assert len(files) != 0

    # We can find a file named "internalerror.html"
    assert (file := next(file for file in files if file.name == "internalerror.html"))
    assert "{{ message }}" in file.read_text()


def test_init_exception_handlers(mock_inginious_page, template_helper, flask_app):
    mock_inginious_page.app = flask_app
    mock_inginious_page.template_helper = template_helper
    init_exception_handlers(mock_inginious_page)


@pytest.mark.parametrize("model, model_description", list(model_names.items()))
def test_handle_validation_error_known_model(model, model_description):
    try:
        model(arg1="foo", arg2="bar")
    except ValidationError as e:
        html, status_code = handle_validation_error(e)
        assert status_code == 500
        assert model_description in html
