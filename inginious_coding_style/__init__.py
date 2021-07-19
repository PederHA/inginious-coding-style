from pathlib import Path
from typing import Any, Dict, List, Optional, OrderedDict, Union, Tuple

from flask import redirect, request
from inginious.client.client import Client
from inginious.frontend.course_factory import CourseFactory
from inginious.frontend.courses import Course
from inginious.frontend.tasks import Task
from inginious.frontend.pages.course_admin.submission import (
    SubmissionPage,
)  # the page we want to modify
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from inginious.frontend.pages.utils import INGIniousAuthPage
from inginious.frontend.plugin_manager import PluginManager
from inginious.frontend.template_helper import TemplateHelper
from pymongo.collection import ReturnDocument
from bson.errors import InvalidId
from werkzeug.exceptions import NotFound, Forbidden, BadRequest
from werkzeug.wrappers.response import Response
from werkzeug.datastructures import ImmutableMultiDict
from pydantic import ValidationError

from .config import PluginConfig, get_config
from .grades import CodingStyleGrades, get_grades
from .logger import get_logger
from ._types import Submission, GradesIn

PLUGIN_PATH = Path(__file__).parent.absolute()
TEMPLATES_PATH = PLUGIN_PATH / "templates"

# The key to store style grade data in the submission's "custom" dict
PLUGIN_KEY = "coding_style"  # use plugin name from config?


class CodingStyleGradesOverview(INGIniousAuthPage):
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
    """Class that implements methods that allow administrators
    to grade the coding style of a submission."""

    _logger = get_logger()

    def __init__(self, config: PluginConfig, *args, **kwargs) -> None:
        self.config = config
        super().__init__(*args, **kwargs)

    def _add_grades_dev(self, submissionid: str) -> Submission:
        grades = {
            "comments": {"grade": 100, "feedback": "very good!"},
            "modularity": {"grade": 100, "feedback": "very good!"},
            "structure": {"grade": 100, "feedback": "very good!"},
            "idiomaticity": {"grade": 100, "feedback": "very good!"},
        }  # type: GradesIn
        return self.add_grades(submissionid, grades)

    def GET_AUTH(self, submissionid: str) -> str:
        """Displays coding style grading page for a specific submission."""
        # Get submission, course and task objects
        submission = self.fetch_submission(submissionid)
        course, task = self.get_course_and_check_rights(
            submission["courseid"], submission["taskid"]
        )

        # Check if submission has existing coding style grades
        # Ensure the submission has a CodingStyleGrades object
        # at ["custom"][PLUGIN_KEY]
        submission = self.ensure_submission_custom_key(submission)
        grades = submission["custom"][PLUGIN_KEY]

        try:
            user_realname = self.user_manager.get_user_realname(
                submission["username"][0]
            )
        except IndexError:
            self._logger.warning(
                f"Unable to find author of submission {submission['_id']}."
            )
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

    def POST_AUTH(self, submissionid: str) -> Response:
        """Adds or updates the coding style grades of a submission."""
        # Parse grades from grading form
        grades = self.parse_form_data(request.form)

        try:
            self.update_submission_grades(submissionid, grades)
        except Exception as e:
            self._logger.exception(
                f"Failed to validate request body for submission {submissionid}: {grades}"
            )
            raise BadRequest("Unable to validate request.")

        # Redirect to updated submission
        return redirect(f"/admin/codingstyle/{submissionid}")

    def parse_form_data(self, form_data: ImmutableMultiDict) -> GradesIn:
        """Transforms flat form data into nested data that can be parsed by `CodingStyleGrades.parse_obj()`

        ### Example:

        >>> form_data.to_dict()
        {
            "comments_grade": "100",
            "comments_feedback": "Very good!"
            "modularity_grade": "50",
            "modularity_feedback": "Needs more functions!"
        }
        >>> parse_form_data(form_data)
        {
            "comments": {
                "grade": "100",
                "feedback": "Very good!",
            },
            "modularity": {
                "grade": "50",
                "feedback": "Needs more functions!",
            }
        }
        """
        form = form_data.to_dict()  # type: Dict[str, str]

        out: GradesIn = {}
        for (k, v) in form.items():
            category, attr = k.split("_")
            try:
                out[category][attr] = v
            except KeyError:
                out[category] = {attr: v}
        return out

    def fetch_submission(self, submissionid: str) -> Submission:
        """Slimmed down version of `SubmissionPage.fetch_submission`.
        Only returns Submission, instead of Tuple[Course, Task, Submission]"""

        try:
            submission = self.submission_manager.get_submission(submissionid, False)
            if not submission:
                raise NotFound(description=_("This submission doesn't exist."))
        except InvalidId as ex:
            self._logger.info("Invalid ObjectId : %s", submissionid)
            raise Forbidden(description=_("Invalid ObjectId."))
        return submission

    def ensure_submission_custom_key(self, submission: Submission) -> Submission:
        """Adds data structure for adding custom grades to a submission.

        Stores existing custom submission data (if it exists) under `submission["custom"]["original"]`,
        if existing custom data is not a dict.

        Updates the submission's database record if coding style grades datastructure
        is added to the submission.

        ### Rationale:

        There is no formal interface for adding custom data to a submission,
        or indeed any specific structure that should be adhered to, so essentially any plugin can
        add whatever they want to the "custom" key as long as it is serializable,
        and can as a result overwrite other plugins' custom submission data with impunity.

        This method makes sure the value for the "custom" key of an INGInious submission is a dict.
        By default the value is an empty string, but if we let this value be a dict,
        multiple plugins can add data to the dict under their own key, which avoids conflicts.

        Of course, this doesn't alleviate the problem of other plugins overwriting our data,
        but it's a convention that should probably be suggested to the INGInious devs.

        ### In practice the result is:

        ```py
        submission = {
            "_id": ...
            "grade": ...
            # ...
            "custom": {
                "coding_style": CodingStyleGrades(...) # our plugin's data
                "other_plugin": ..., # other plugin's data
            }
        }
        ```
        """

        if not submission.get("custom"):
            submission["custom"] = {}
        elif not isinstance(submission["custom"], dict):
            submission["custom"] = {"original": submission["custom"]}
            # TODO: find out how to get id value from MongoDB ObjectId object
            self._logger.info(
                f"Stored previous custom value under submission['custom'][original] for submission {submission}"
            )

        submission_modified = False
        g = submission["custom"].get(PLUGIN_KEY)
        try:
            # Try to parse existng grades
            grades = get_grades(g)
        except ValidationError:
            # Create new grades from enabled config
            grades = get_grades(self.config.enabled)
            submission_modified = True

        # Ensure all grading categories are added to the submission's custom grades
        for category in self.config.enabled.values():
            if category not in grades:
                grades.add_category(category)
                submission_modified = True

        submission["custom"][PLUGIN_KEY] = grades

        if submission_modified:
            self._update_submission(submission)

        # From here, we can be certain submission["custom"][PLUGIN_KEY]
        # is a CodingStyleGrades object

        return submission

    def update_submission_grades(
        self, submissionid: str, grades_data: GradesIn
    ) -> Submission:
        """Attempts to update a submission with a new set of coding style grades.

        Raises `ValidationError` if grades cannot be validated.

        Parameters
        ----------
        submissionid : str
            The submission ID.
        grades_data : GradesIn
            New grades from grading form on the WebApp.

        Returns
        -------
        Submission
            Updated submission
        """
        # Get the submission
        submission = self.submission_manager.get_submission(
            submissionid, user_check=False
        )
        submission = self.ensure_submission_custom_key(submission)

        # Add grade data to the submission:
        #
        # NOTE: This is by far the worst side-effect of using Pydantic models,
        # and then doing partial updates to a dynamic number of items.
        # We by necessity have to copy the grades from the plugin config
        # and then convert them to a dict, so we can then use dict.update()
        # with the new grades we receive from the webapp form.
        #
        # We end up with the following:
        #   * Retrieves a copy of the currently enabled categories from the config (self.config.dict()["enabled"])
        #   * Iterates through the grade data from the webapp form (grades_data)
        #   * Updates each enabled grade with data from the webapp form
        #   * Adds the new grades to the submission for each category (overwriting the old grades)
        #   * Updates the database with the new custom grades
        conf = self.config.dict()
        grades = conf["enabled"]  # type: Dict[str, dict]
        for category in grades_data:
            if category not in grades:
                continue  # skip disabled grades
            grades[category].update(grades_data[category])
        # Validate new grades and add them to the submission
        # If validation fails, ValidationError is raised
        submission["custom"][PLUGIN_KEY] = get_grades(grades)

        return self._update_submission(submission)

    def _update_submission(self, submission: Submission) -> Submission:
        """Finds an existing submission and updates it with new data.

        Returns updated submission.
        """
        # NOTE: Optional[Submission] type annotation? We should never be in a situation
        # where we are able to call this method on a nonexistent submission, though.

        # Convert grades object to dict if it is a CodingStyleGrades instance
        # so that MongoDB is able to store it.
        grades = submission["custom"][PLUGIN_KEY]
        if isinstance(grades, CodingStyleGrades):
            submission["custom"][PLUGIN_KEY] = grades.dict()

        return self.database.submissions.find_one_and_update(
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


def task_list_item(
    course: Course,
    taskid: str,
    task: Task,
    tasks_data: Any,
    template_helper: TemplateHelper,
) -> str:
    """Displays a progress bar denoting the current coding style grade for a given task."""
    return "<p>roflmao</p>"


def task_menu(course: Course, task: Task, template_helper: TemplateHelper) -> str:
    return "<p>lol</p>"


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
            categories:
                - id: <Category id>
                name: <Name of category>
                description: <Category description>

    *name*
    Display name of the plugin

    *enabled*
    Which coding style categories to enable. Omitting this parameter enables all categories.

    *categories*
    Custom category definitions. Each category must contain the following:

        *id*
        Unique ID of category

        *name*
        Name of category

        *description*
        Category description
    """
    config = get_config(conf)

    # Add coding style grade progress bar hook
    plugin_manager.add_hook("task_list_item", task_list_item)

    # Show coding style grade on task menu
    plugin_manager.add_hook("task_menu", task_menu)

    # Add button to course menu
    plugin_manager.add_hook("course_admin_menu", course_admin_menu)
    plugin_manager.add_hook("submission_admin_menu", submission_admin_menu)

    # Grading interface for admins  (NYI)
    plugin_manager.add_page(
        "/admin/codingstyle/<submissionid>",
        CodingStyleGrading.as_view("codingstyleadmin", config),
    )

    # User grade overview for a specific course  (NYI)
    plugin_manager.add_page(
        "/course/<courseid>/codingstyle",
        CodingStyleGradesOverview.as_view("codingstyleoverview"),
    )

    # Coding Style Grade view for a specific user submission  (NYI)
    plugin_manager.add_page(
        "/submission/<submissionid>/codingstyle",
        CodingStyleGrading.as_view("codingstylesubmission", config),
    )
