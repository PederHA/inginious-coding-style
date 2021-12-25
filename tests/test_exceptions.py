from pathlib import Path
from typing import List, Type

import pytest
from flask.app import Flask
from inginious.frontend.pages.utils import INGIniousPage
from inginious.frontend.template_helper import TemplateHelper
from pydantic.error_wrappers import ValidationError
from pydantic.main import BaseModel

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


def test_init_exception_handlers(
    mock_inginious_page: INGIniousPage,
    template_helper: TemplateHelper,
    flask_app: Flask,
):
    mock_inginious_page.app = flask_app
    mock_inginious_page.template_helper = template_helper
    init_exception_handlers(mock_inginious_page)


@pytest.mark.parametrize("model, model_description", list(model_names.items()))
def test_handle_validation_error_known_model(
    model: Type[BaseModel], model_description: str
):
    try:
        model(arg1="foo", arg2="bar")
    except ValidationError as e:
        html, status_code = handle_validation_error(e)
        assert status_code == 500
        assert model_description in html
