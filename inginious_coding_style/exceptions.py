from pathlib import Path
from typing import Tuple

from inginious.frontend.pages.utils import INGIniousPage
from inginious.frontend.template_helper import TemplateHelper
from pydantic import ValidationError

from inginious import frontend

from .grades import CodingStyleGrades, GradesIn, GradingCategory
from .logger import get_logger
from .submission import Submission

# Another global B-)
TEMPLATE_HELPER: TemplateHelper = None
TEMPLATE_FOLDER = (
    Path(frontend.__file__).parent / "templates"
)  # TODO: remove double declaration

# Human-readable names/descriptions of the models
model_names = {
    GradingCategory: "Grading category",
    # GradesIn: "Grades from grading form",  # this shouldn't be here?
    Submission: "Submission",
    CodingStyleGrades: "Coding Style Grades",
}

# def format_valiation_error(exc: ValidationError) -> str:
#     for error in exc.raw_errors:
#         if isinstance(error.exc, MissingError):


def handle_validation_error(exc: ValidationError) -> Tuple[str, int]:
    get_logger().error(f"A Pydantic validation error occured: {exc}")
    return (
        TEMPLATE_HELPER.render(
            "internalerror.html",
            message=f"Failed to validate {model_names.get(exc.model, exc.model)}.",
        ),
        500,
    )


def init_exception_handlers(obj: INGIniousPage) -> None:
    # This function can be expanded with additional exception handlers
    global TEMPLATE_HELPER
    if not TEMPLATE_HELPER:
        TEMPLATE_HELPER = obj.template_helper
    obj.app.register_error_handler(ValidationError, handle_validation_error)
