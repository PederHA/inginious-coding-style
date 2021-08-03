import time
from pathlib import Path
from typing import Any, Dict, List, OrderedDict, Union

from bson.errors import InvalidId
from flask import redirect, request
from inginious.client.client import Client
from inginious.frontend.course_factory import CourseFactory
from inginious.frontend.courses import Course
from inginious.frontend.pages.course_admin.submission import SubmissionPage
from inginious.frontend.pages.utils import INGIniousAuthPage
from inginious.frontend.plugin_manager import PluginManager
from inginious.frontend.tasks import Task
from inginious.frontend.template_helper import TemplateHelper
from pydantic import ValidationError
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.exceptions import BadRequest, Forbidden, InternalServerError, NotFound
from werkzeug.wrappers.response import Response

from ._types import GradesIn
from .config import PluginConfig, get_config
from .exceptions import init_exception_handlers
from .grades import add_config_categories, get_grades
from .logger import get_logger
from .submission import Submission, get_submission
from .utils import (
    get_best_submission,
    get_submission_authors_realname,
    get_submission_timestamp,
)

__version__ = "1.1.0"

PLUGIN_PATH = Path(__file__).parent.absolute()
TEMPLATES_PATH = PLUGIN_PATH / "templates"

# Makes plugin config available globally
PLUGIN_CONFIG: PluginConfig = None  # type: ignore


class StudentSubmissionCodingStyle(INGIniousAuthPage):
    """Displays a detailed view of coding style grades for a single submission
    made by a student."""

    _logger = get_logger()

    def __init__(self, config: PluginConfig, *args, **kwargs) -> None:
        self.config = config
        super().__init__(*args, **kwargs)
        init_exception_handlers(self)

    def GET_AUTH(self, submissionid: str) -> str:
        """Displays all coding style grades for a given course for a user."""
        submission = self.get_submission(submissionid)
        course = self.get_course(submission)
        task = self.get_task(submission, course)

        if not submission.custom.coding_style_grades:
            raise NotFound("Submission has no coding style grades.")

        names = get_submission_authors_realname(self, submission)
        submitted_on = get_submission_timestamp(submission)

        return self.template_helper.render(
            "stylegrade.html",
            template_folder=TEMPLATES_PATH,
            submission_authors=names,
            submitted_on=submitted_on,
            user_manager=self.user_manager,
            course=course,
            task=task,
            submission=submission,
            grades=submission.custom.coding_style_grades,
            config=self.config,
        )

    def get_course(self, submission: Submission) -> Course:
        try:
            course = self.course_factory.get_course(submission.courseid)
        except Exception as e:
            if not submission.courseid:
                self._logger.error(
                    f"Submission {submission._id} is not associated with any course. Has the submission been corrupted?"
                )
            else:
                self._logger.error(
                    f"Unable to find course with course ID {submission.courseid}. Has it been deleted?"
                )
            raise InternalServerError("Unable to display submission.")
        return course

    def get_task(self, submission: Submission, course: Course) -> Task:
        try:
            task = course.get_task(submission.taskid)
        except Exception as e:
            if not submission.taskid:
                self._logger.error(
                    f"Submission {submission._id} is not associated with a task. Has the submission been corrupted?"
                )
            else:
                self._logger.error(
                    f"Unable to find task with task ID {submission.taskid}. Has it been deleted?"
                )
            raise InternalServerError("Unable to display submission.")
        return task

    def get_submission(self, submissionid: str) -> Submission:
        """Slimmed down version of SubmissionPage.fetch_submission.
        Only returns Submission, instead of Tuple[Course, Task, OrderedDict]"""

        try:
            submission = self.submission_manager.get_submission(submissionid, False)
            if not submission:
                raise NotFound(description=_("This submission doesn't exist."))
        except InvalidId as ex:
            self._logger.info("Invalid ObjectId : %s", submissionid)
            raise Forbidden(description=_("Invalid ObjectId."))
        return get_submission(submission)


class CodingStyleGrading(SubmissionPage):
    """Page that lets administrators grade the coding style of a submission."""

    _logger = get_logger()

    def __init__(self, config: PluginConfig, *args, **kwargs) -> None:
        self.config = config
        super().__init__(*args, **kwargs)
        init_exception_handlers(self)

    def GET_AUTH(self, submissionid: str) -> str:
        """Displays coding style grading page for a specific submission."""
        course, task, sub = self.fetch_submission(submissionid)

        # Validate submission and check if it has coding style grades
        submission = get_submission(sub)
        grades = submission.custom.coding_style_grades
        if not grades:
            grades = get_grades(self.config.enabled)
        # Add any missing grading categories
        grades = add_config_categories(grades, self.config)
        submission.custom.coding_style_grades = grades

        authors = get_submission_authors_realname(self, submission)
        submitted_on = get_submission_timestamp(submission)

        # Check if page is displayed after updating submission grades
        # Display alert denoting success of update:
        # None = no msg, True = success msg, False = failure msg
        success = request.args.get("success")

        return self.template_helper.render(
            "grade_submission.html",
            template_folder=TEMPLATES_PATH,
            user_manager=self.user_manager,
            submitted_on=submitted_on,
            authors=authors,
            course=course,
            task=task,
            submission=submission,
            grades=submission.custom.coding_style_grades,
            config=self.config,
            success=success,
        )

    def POST_AUTH(self, submissionid: str) -> Response:
        """Adds or updates the coding style grades of a submission."""
        # Parse grades from grading form
        grades = self.parse_form_data(request.form)

        success = True
        try:
            self.update_submission_grades(submissionid, grades)
        except Exception as e:
            self._logger.exception(
                f"Failed to validate request body for submission {submissionid}: {grades}"
            )
            success = False

        # Redirect to updated submission
        return redirect(
            f"/admin/codingstyle/submission/{submissionid}?success={1 if success else 0}"
        )

    def put(self, submissionid: str, *args, **kwargs) -> Union[str, Response]:
        """We (ab)use the superclass `flask.views.MethodView` here to add a PUT rule for the view.

        INGInious only implements their own `GET_AUTH` and `POST_AUTH` methods,
        so we use this method to add support for partial updates of Coding Style Grades,
        such as updating only a single category or removing a category altogether.

        Right now, the only supported operation is removing a grading category
        from a submission.
        """

        # Retrieve submission, then check permissions.
        submission = self.submission_manager.get_submission(
            submissionid, user_check=False
        )
        self.get_course_and_check_rights(submission["courseid"], submission["taskid"])

        # Check if a category should be removed
        if category := request.args.get("remove"):
            self.remove_category_from_submission(submission, category=category)
            return Response(
                "ok",
                # Use custom htmx HTTP header to prompt browser to refresh page
                # Source: https://htmx.org/docs/#response-headers
                headers={"HX-Refresh": "true"},
            )
        # TODO: add other PUT operations
        raise BadRequest("Unsupported operation")

    def remove_category_from_submission(
        self, submission: Submission, category: str
    ) -> None:
        """Removes a category from a submission.
        Does nothing if submission does not have a category with that name.

        Parameters
        ----------
        submission : Submission
            The submission to modify.
        category : str
            Name of the category to remove.
        """
        submission.custom.coding_style_grades.remove_category(category)
        self._update_submission(submission)

    def parse_form_data(self, form_data: ImmutableMultiDict) -> GradesIn:
        """Transforms flat form data into nested data that can be parsed
        by `CodingStyleGrades.parse_obj()`

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

    def update_submission_grades(
        self, submissionid: str, grades_data: GradesIn
    ) -> None:
        """Attempts to update a submission with a new set of coding style grades.

        Raises `ValidationError` if grades cannot be validated.

        Parameters
        ----------
        submissionid : `str`
            ID of the submission to update grades of.
        grades_data : `GradesIn`
            Input from grading form on the WebApp.

        Returns
        -------
        `Submission`
            Updated submission

        Raises
        -------
        `ValidationError`
            Unable to validate new grades.
        """
        # Get the submission
        sub = self.submission_manager.get_submission(submissionid, user_check=False)
        submission = get_submission(sub)

        # Add grade data to the submission
        #
        # NOTE:
        # This is by far the worst side-effect of using Pydantic with a dynamic
        # model, and having to do partial updates to a variable number of items.
        #
        # We by necessity have to copy the grading categories from the plugin config
        # and then convert them to a dict, so we can then use dict.update()
        # with the new grades we receive from the webapp form. After updating the
        # dict, we convert it back to a CodingStyleGrades object.
        #
        # This is clunky, but it still executes very quickly though.
        #
        # We end up doing the following:
        #   * Retrieve a copy of the currently enabled categories from the config (self.config.dict()["enabled"])
        #   * Iterate through the grade data from the webapp form (grades_data)
        #   * Update each enabled grade with data from the webapp form
        #   * Add the new grades to the submission for each category (overwriting the old grades)
        #   * Update the database with the new custom grades
        conf = self.config.dict()
        grades = conf["enabled"]  # type: Dict[str, dict]
        for category in grades_data:
            if category not in grades:
                continue  # skip disabled grades
            grades[category].update(grades_data[category])
        # Validate new grades and add them to the submission
        # If validation fails, ValidationError is raised
        submission.custom.coding_style_grades = get_grades(grades)

        self._update_submission(submission)

    def _update_submission(self, submission: Submission) -> None:
        """Finds an existing submission and updates it with new data.

        Returns updated submission, or None if submission was not found.
        """
        if self.config.experimental.merge_grades:
            self.merge_submission_grades(submission)

        self.database.submissions.find_one_and_update(
            {"_id": submission._id},
            {"$set": submission.dict()},
        )

    def merge_submission_grades(self, submission: Submission) -> None:
        """
        ## WARNING: EXPERIMENTAL

        Finds the mean of submission base grade and coding style grade
        and updates its entry in the DB collection 'user_tasks', which is a collection
        that records top submissions for every user for every task.

        NOTE: This method has no effect if the submission that is being graded is
        _not_ the user's top submission for the given task. This is due to the way
        INGInious seems to store a sort of "meta-submission" in the 'user_tasks'
        collection, which keeps track of the user's best grade for a specific task and
        the number of submissions they have made for that task, and the ID of their
        top submission. It is that grade that is displayed on the course's task list,
        and thus it is also the one we are modifying in this method.
        Furthermore, it makes no sense to grade a submission that ISN'T the user's
        best submission, so that is also relevant!

        Submission's new grade calculation:
        `merged = (base_grade + style_mean) / 2`
        """
        grades = submission.custom.coding_style_grades
        base_grade = submission.grade
        style_mean = grades.get_mean(self.config, round_grade=False)
        mean_grade = round(base_grade + style_mean) / 2

        # Update the 'user_tasks' collection (where top submissions are stored)
        self.database.user_tasks.find_one_and_update(
            {"submissionid": submission._id}, {"$set": {"grade": mean_grade}}
        )


def submission_admin_menu(
    course: Course, task: Task, submission: Submission, template_helper: TemplateHelper
) -> str:
    return template_helper.render(
        "submission_admin_menu.html",
        template_folder=TEMPLATES_PATH,
        submission=submission,
    )


def task_list_item(
    course: Course,
    task: Task,
    tasks_data: Any,
    template_helper: TemplateHelper,
) -> str:
    """Displays a progress bar denoting the current coding style grade for a given task."""
    # TODO: optimize. Cache best submission?
    best_submission = get_best_submission(task)
    if not best_submission or not best_submission.custom.coding_style_grades:
        return ""

    grades = best_submission.custom.coding_style_grades

    return template_helper.render(
        "task_list_item.html",
        template_folder=TEMPLATES_PATH,
        grade=grades.get_mean(PLUGIN_CONFIG),
        submission=best_submission,
    )


def task_menu(course: Course, task: Task, template_helper: TemplateHelper) -> str:
    best_submission = get_best_submission(task)
    # Render blank if no submission or no coding style grades are found
    if best_submission is None or not best_submission.custom.coding_style_grades:
        return ""

    return template_helper.render(
        "task_menu.html",
        template_folder=TEMPLATES_PATH,
        submission=best_submission,
    )


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
            experimental:
                merge_grades: false

    *name*
    Display name of the plugin

    *enabled*
    List of grading category IDs to enable. Omitting this parameter enables all default categories.

    *categories*
    Custom category definitions. Each category must contain the following:

        *id*
        Unique ID of category

        *name*
        Name of category

        *description*
        Category description

    *experimental*
    Experimental features to enable. These are not guaranteed to be robust,
    and are subject to change in future versions.

        *merge_grades*
        Recalculates a submission's grade based on the mean of automated grade
        and coding style grades. The weighting is 50% automated grade + 50% style grade average.
    """
    # Get config and make it global
    config = get_config(conf)
    global PLUGIN_CONFIG
    PLUGIN_CONFIG = config

    # Display coding style grades in list of tasks for a course
    plugin_manager.add_hook("task_list_item", task_list_item)

    # Show button to navigate to detailed coding style grades for a submission
    plugin_manager.add_hook("task_menu", task_menu)

    # Show button to navigate to coding style grading page for admins
    plugin_manager.add_hook("submission_admin_menu", submission_admin_menu)

    # Grading interface for admins
    plugin_manager.add_page(
        "/admin/codingstyle/submission/<submissionid>",
        CodingStyleGrading.as_view("codingstyleadmin", config),
    )

    # # User grade overview for a specific course  (NYI)
    # plugin_manager.add_page(
    #     "/course/<courseid>/codingstyle",
    #     CodingStyleGradesOverview.as_view("codingstyleoverview"),
    # )

    # Coding Style Grade view for a specific user submission
    plugin_manager.add_page(
        "/submission/<submissionid>/codingstyle",
        StudentSubmissionCodingStyle.as_view("codingstylesubmission", config),
    )
