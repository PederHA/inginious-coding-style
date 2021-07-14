from pathlib import Path
from typing import Any, Dict, List, Optional, OrderedDict, Union, Tuple

import flask
from inginious.client.client import Client
from inginious.frontend.course_factory import CourseFactory
from inginious.frontend.courses import Course
from inginious.frontend.pages.course_admin.submission import (
    SubmissionPage,
)  # the page we want to modify
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from inginious.frontend.pages.utils import INGIniousAuthPage
from inginious.frontend.plugin_manager import PluginManager
from inginious.frontend.template_helper import TemplateHelper
from pymongo.collection import ReturnDocument
from bson.errors import InvalidId
from werkzeug.exceptions import NotFound, Forbidden

from .config import PluginConfig
from .grades import CodingStyleGrade, get_grades
from .logger import get_logger
from ._types import Submission, GradesIn

PLUGIN_PATH = Path(__file__).parent.absolute()
TEMPLATES_PATH = PLUGIN_PATH / "templates"

# The key to store style grade data in the submission's "custom" dict
PLUGIN_KEY = "coding_style"


class CodingStyleGradeOverview(INGIniousAuthPage):
    def GET_AUTH(self) -> str:
        """Displays all coding style grades for a given course for a user."""
        return self.user_manager.session_realname()

    def fetch_submission(self, submissionid: str) -> dict:
        """Slimmed down version of SubmissionPage.fetch_submission.
        Only returns dict (submission), instead of Tuple[Course, Task, dict]"""

        try:
            submission = self.submission_manager.get_submission(submissionid, False)
            if not submission:
                raise NotFound(description=_("This submission doesn't exist."))
        except InvalidId as ex:
            self._logger.info("Invalid ObjectId : %s", submissionid)
            raise Forbidden(description=_("Invalid ObjectId."))
        return submission


class CodingStyleGrading(INGIniousAdminPage):
    """Page to set"""

    _logger = get_logger()

    def __init__(self, config: PluginConfig, *args, **kwargs) -> None:
        self.config = config
        super().__init__(*args, **kwargs)

    def GET_AUTH(self, submissionid: str) -> str:
        """GET request"""
        submission = self.fetch_submission(submissionid)
        course, task = self.get_course_and_check_rights(
            submission["courseid"], submission["taskid"]
        )
        grades = self.get_submission_grades(submission)
        if not grades:
            submission = self._add_grades_dev(submissionid)
        try:
            user_realname = self.user_manager.get_user_realname(
                submission["username"][0]
            )
        except IndexError:
            self._logger.warning(f"Submission {submission['_id']} has no author.")
            user_realname = "Unknown user"

        return self.template_helper.render(
            "grade_submission.html",
            template_folder=TEMPLATES_PATH,
            # TODO: check how this works with group submissions
            user_realname=user_realname,
            course=course,
            task=task,
            submission=submission,
            grades=grades,
            config=self.config,
        )

    def _add_grades_dev(self, submissionid: str) -> Submission:
        grades = {
            "comments": {"grade": 100, "feedback": "very good!"},
            "modularity": {"grade": 100, "feedback": "very good!"},
            "structure": {"grade": 100, "feedback": "very good!"},
            "idiomaticity": {"grade": 100, "feedback": "very good!"},
        }  # type: GradesIn
        return self.add_grades(submissionid, grades)

    def POST_AUTH(self, submissionid: str) -> None:
        # PSEUDOCODE:

        # Assume request body contains the following data
        req_body = {
            "comments": {"grade": 100, "feedback": "very good!"},
            "modularity": {"grade": 100, "feedback": "very good!"},
            "structure": {"grade": 100, "feedback": "very good!"},
            "idiomaticity": {"grade": 100, "feedback": "very good!"},
        }  # type: GradesIn

        req_body = self.parse_form_data(flask.request.form)

        try:
            self.add_grades(submissionid, req_body)
        except Exception as e:
            self._logger.exception(
                f"Failed to validate request body for submission {submissionid}"
            )
            return

    def parse_form_data(self, form_data: Dict[str, str]) -> GradesIn:
        # The type of form_data is actually werkzeug.datastructures.ImmutableMultiDict
        form = form_data.to_dict()  # type: ignore

        out: GradesIn = {}
        for (k, v) in form.items():  # type: Tuple[str, str]
            category, attr = k.split("_")
            try:
                out[category][attr] = v
            except KeyError:
                out[category] = {attr: v}
        return out

    def fetch_submission(self, submissionid: str) -> Submission:
        """Slimmed down version of SubmissionPage.fetch_submission.
        Only returns dict (submission), instead of Tuple[Course, Task, dict]"""

        try:
            submission = self.submission_manager.get_submission(submissionid, False)
            if not submission:
                raise NotFound(description=_("This submission doesn't exist."))
        except InvalidId as ex:
            self._logger.info("Invalid ObjectId : %s", submissionid)
            raise Forbidden(description=_("Invalid ObjectId."))
        return submission

    def get_best_submission(
        self, courseid: str, taskid: str, username: str
    ) -> list:  # list what?
        return list(
            self.database.user_tasks.find(
                {"username": username, "courseid": courseid, "taskid": taskid},
                {"submissionid": 1, "_id": 0},
            )
        )

    def ensure_submission_custom_key(self, submission: Submission) -> Submission:
        """Adds data structure for adding custom grades to a submission if it doesn't have one.

        Stores existing data (if it exists) under `submission["custom"]["original"]`,
        if existing custom data is not a dict.

        ### Rationale:

        There is no formal interface for adding custom data to a submission,
        or indeed any specific structure that should be adhered to, so essentially any plugin can
        add whatever they want to the "custom" key as long as it is serializable,
        and can as a result overwrite other plugins' custom submission data with impunity.

        This method makes sure the value for the "custom" key of an INGInious submission is a dict.
        By default the value is an empty string, but if we let this value be a dict,
        multiple plugins can add data to the dict under their own key, which avoids conflicts.

        Of course, this doesn't alleviate the problem of other plugins overwriting our data,
        but it's a convention that should probably be submitted as a pull request.

        ### In practice:

        ```py
        submission = {
            "_id": ...
            "grade": ...
            # ...
            "custom": {
                "coding_style": {
                    # our plugin's data
                },
                "other_plugin": {
                    # other plugin's data
                }
            }
        }
        ```
        """

        if not submission.get("custom"):
            submission["custom"] = {}
        elif not isinstance(submission["custom"], dict):
            submission["custom"] = {"original": submission["custom"]}
            # TODO: find out how to get int value from MongoDB ObjectId object
            self._logger.info(
                f"Stored previous custom value under submission['custom'][original] for submission {submission}"
            )

        return submission

    def add_grades(self, submissionid: str, grade_data: GradesIn) -> Submission:
        # NOTE: A LOT OF PSEUDOCODE!

        # Get the submission
        submission = self.submission_manager.get_submission(
            submissionid, user_check=False
        )

        # Validate data
        grades = CodingStyleGrade(**grade_data)

        # Make sure custom grades can be added to the submission
        submission = self.ensure_submission_custom_key(submission)

        # Add grade data
        submission["custom"][PLUGIN_KEY] = grades.dump_dict()

        updated = self.database.submissions.find_one_and_update(
            {"_id": submission["_id"]},
            {"$set": submission},
            return_document=ReturnDocument.AFTER,
        )  # type: Submission
        return updated

    def get_submission_grades(
        self, submission: Submission
    ) -> Optional[CodingStyleGrade]:
        """Attempts to retrieve a `CodingStyleGrade` for a given submission."""
        submission = self.ensure_submission_custom_key(submission)
        grades = submission["custom"].get(PLUGIN_KEY)
        if not grades:
            return None
        return get_grades(grades)  # creates CodingStyleGrade object

    def get_submissions(
        self, courseid: str = "tutorial", taskid: str = "04_run_student"
    ) -> List[Submission]:
        # NOTE: PSEUDOCODE!
        # Demonstrates how to retrieve all submissions for a given task

        # get the task we want to find submissions for
        task = self.course_factory.get_task(courseid, taskid)

        # get all submissions
        submissions = self.submission_manager.get_user_submissions(
            task
        )  # type: List[Submission]

        return submissions

    def update_submission(self, submission: Submission) -> None:
        updated = self.database.submissions.find_one_and_update(
            {"_id": submission["_id"]},
            {"$set": submission},
            return_document=ReturnDocument.AFTER,
        )


def submission_admin_menu(
    course: Course, submission: Submission, template_helper: TemplateHelper
) -> Optional[str]:
    info = course.get_descriptor()
    get_logger().info("hello!")
    return template_helper.render(
        "submission_admin_menu.html",
        template_folder=TEMPLATES_PATH,
        submission=submission,
    )


def course_admin_menu(course: Course) -> Tuple[str, str]:
    print(course)
    return ("contest", '<i class="fa fa-trophy fa-fw"></i>&nbsp; Contest')


def init(
    plugin_manager: PluginManager,
    course_factory: CourseFactory,
    client: Client,
    conf: OrderedDict[str, Union[str, List[str]]],
):
    """
    Allows teachers to grade several aspect of a student submission's code style.

    Available configuration:
    ::

        plugins:
        -   plugin_module: inginious_coding_style
            name: "INGInious Coding Style"
            enabled:
                - comments
                - modularity
                - structure
                - idiomaticity

    *name*
    Display name of the plugin

    *enabled*
    Which coding style categories to enable. Omitting this parameter enables all categories.

    """
    config = PluginConfig(**conf)

    # Add button to course menu
    plugin_manager.add_hook("course_admin_menu", course_admin_menu)
    plugin_manager.add_hook("submission_admin_menu", submission_admin_menu)

    # We either do this, or directly modify TemplateHelper._base_helpers:
    # plugin_manager._flask_app.template_helper.add_other(
    #     "submission_admin_menu", lambda **kwargs: submission_admin_menu(**kwargs)
    # )

    # Grading interface for admins  (NYI)
    plugin_manager.add_page(
        "/admin/codingstyle/<submissionid>",
        CodingStyleGrading.as_view("codingstyleadmin", config),
    )

    # User grade overview for a specific course  (NYI)
    plugin_manager.add_page(
        "/course/<courseid>/codingstyle",
        CodingStyleGradeOverview.as_view("codingstyleoverview"),
    )

    # Coding Style Grade view for a specific user submission  (NYI)
    plugin_manager.add_page(
        "/submission/<submissionid>/codingstyle",
        CodingStyleGrading.as_view("codingstylesubmission", config),
    )
