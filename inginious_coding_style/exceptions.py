from pathlib import Path
from typing import Tuple

from inginious.frontend.pages.utils import INGIniousPage
from inginious.frontend.template_helper import TemplateHelper
from pydantic import ValidationError

from inginious import frontend

from .grades import CodingStyleGrades, GradingCategory
from .logger import get_logger
from .submission import Submission

TEMPLATE_HELPER: TemplateHelper = None
TEMPLATE_FOLDER = Path(frontend.__file__).parent / "templates"


# Human-readable names/descriptions of the models
# TODO: Move these names to the models themselves?
model_names = {
    GradingCategory: "Grading category",
    Submission: "Submission",
    CodingStyleGrades: "Coding Style Grades",
}


def handle_validation_error(exc: ValidationError) -> Tuple[str, int]:
    get_logger().error(f"A Pydantic validation error occured: {exc}")
    return (
        TEMPLATE_HELPER.render(
            "internalerror.html",
            message=f"Failed to validate {model_names.get(exc.model, exc.model)}.",  # type: ignore
        ),
        500,  # status code
    )


def init_exception_handlers(obj: INGIniousPage) -> None:
    # This function can be expanded with additional exception handlers
    global TEMPLATE_HELPER
    if TEMPLATE_HELPER is not None:
        return
    TEMPLATE_HELPER = obj.template_helper
    obj.app.register_error_handler(ValidationError, handle_validation_error)
