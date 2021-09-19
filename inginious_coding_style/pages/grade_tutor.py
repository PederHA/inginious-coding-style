from typing import Union

from flask import redirect, request
from werkzeug import Response
from werkzeug.exceptions import BadRequest

from ..grades import add_config_categories, get_grades
from ..mixins import AdminPageMixin, SubmissionMixin
from ..utils import parse_form_data
from .base import BasePluginPage


class CodingStyleGradingPage(BasePluginPage, SubmissionMixin, AdminPageMixin):
    """Page that lets administrators grade the coding style of a submission."""

    def GET_AUTH(self, submissionid: str) -> str:
        """Displays coding style grading page for a specific submission."""
        course, task, submission = self.get_submission(submissionid)
        self.check_course_privileges(course)

        # get grades from submission (if exists) or create new from enabled config categories
        grades = submission.custom.coding_style_grades
        if not grades:
            grades = get_grades(self.config.enabled)
        else:
            # Add any missing grading categories to existing grades
            # if submission was graded prior to any new categories being enabled
            grades = add_config_categories(grades, self.config)

        metadata = self.get_submission_metadata(submission)

        # Check if page is displayed after updating submission grades
        # Display alert denoting success of update:
        # None = no msg, True = success msg, False = failure msg
        success = request.args.get("success")

        return self.template_helper.render(
            "grade_submission.html",
            template_folder=self.templates_path,
            user_manager=self.user_manager,
            metadata=metadata,
            course=course,
            task=task,
            submission=submission,
            grades=grades,
            config=self.config,
            success=success,
        )

    def POST_AUTH(self, submissionid: str) -> Response:
        """Adds or updates the coding style grades of a submission."""
        # Parse grades from grading form
        grades = parse_form_data(request.form)
        course, task, submission = self.get_submission(submissionid)
        self.check_course_privileges(course)

        success = 1
        try:
            self.update_submission_grades(submission, grades)
        except Exception as e:
            self._logger.exception(
                f"Failed to validate request body for submission {submissionid}: {grades}",
                exc_info=e,
            )
            success = 0

        return redirect(
            f"/admin/codingstyle/submission/{submissionid}?success={success}"
        )

    def patch(self, submissionid: str, *args, **kwargs) -> Union[str, Response]:
        """Performs a partial update of a submission."""
        # We (ab)use the superclass `flask.views.MethodView` here to add a PUT rule for the view.
        #
        # INGInious only implements their own `GET_AUTH` and `POST_AUTH` methods,
        # so we use this method to add support for partial updates of Coding Style Grades,
        # such as updating only a single category or removing a category altogether.
        #
        # Right now, the only supported operation is removing a grading category
        # from a submission.

        course, task, submission = self.get_submission(submissionid)
        self.check_course_privileges(course)

        # Check if a category should be removed
        if category := request.args.get("remove"):
            self.remove_category_from_submission(submission, category)
            return Response(
                "ok",
                # Use custom htmx HTTP header to prompt browser to refresh page
                # Source: https://htmx.org/docs/#response-headers
                headers={"HX-Refresh": "true"},
            )
        # TODO: add other PUT operations
        raise BadRequest("Unsupported operation")

    def delete(self, submissionid: str, *args, **kwargs) -> Response:
        """Removes coding style grades from a submission."""
        course, task, submission = self.get_submission(submissionid)
        self.check_course_privileges(course)
        if not submission.custom.coding_style_grades:
            raise BadRequest("Submission has no coding style grades.")

        submission.delete_coding_style_grades()
        self.update_submission(submission)

        return Response(
            "ok",
            # https://htmx.org/docs/#response-headers
            headers={"HX-Refresh": "true"},
        )
