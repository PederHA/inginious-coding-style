from inginious.frontend.pages.utils import INGIniousPage
from pydantic import ValidationError
from werkzeug.exceptions import InternalServerError

from .logger import get_logger


def handle_validation_error(exc: ValidationError) -> None:
    get_logger().error("A Pydantic validation error occured", exc_info=exc)
    raise InternalServerError("Validation error")


def init_exception_handlers(obj: INGIniousPage) -> None:
    # This function can be expanded with additional exception handlers
    obj.app.register_error_handler(ValidationError, handle_validation_error)
