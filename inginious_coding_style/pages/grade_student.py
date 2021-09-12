from werkzeug.exceptions import NotFound

from ..mixins import SubmissionMixin
from .base import BasePluginPage


class StudentSubmissionCodingStylePage(BasePluginPage, SubmissionMixin):
    """Displays a detailed view of coding style grades for a single submission
    made by a student."""

    def GET_AUTH(self, submissionid: str) -> str:
        """Displays all coding style grades for a given course for a user."""
        course, task, submission = self.get_submission(submissionid, user_check=True)

        if not submission.custom.coding_style_grades:
            raise NotFound("Submission has no coding style grades.")

        metadata = self.get_submission_metadata(submission)

        return self.template_helper.render(
            "stylegrade.html",
            template_folder=self.templates_path,
            metadata=metadata,
            user_manager=self.user_manager,
            course=course,
            task=task,
            submission=submission,
            grades=submission.custom.coding_style_grades,
            config=self.config,
        )
