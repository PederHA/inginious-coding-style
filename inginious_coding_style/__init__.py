from pathlib import Path
from typing import List, Optional, OrderedDict

from inginious.client.client import Client
from inginious.frontend.course_factory import CourseFactory
from inginious.frontend.courses import Course
from inginious.frontend.pages.course_admin.submission import (
    SubmissionPage,
)  # the page we want to modify
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from inginious.frontend.plugin_manager import PluginManager
from inginious.frontend.template_helper import TemplateHelper
from pymongo.collection import ReturnDocument

from .config import PluginConfig
from .grades import CodingStyleGrade, get_grade
from .logger import get_logger

PLUGIN_PATH = Path(__file__).parent.absolute()
TEMPLATES_PATH = PLUGIN_PATH / "templates"

# The key to store style grade data in the dict
# stored
CUSTOM_KEY = "coding_style"


class CodingStyleGrading(INGIniousAdminPage):
    """Page to set"""

    def GET_AUTH(self, courseid: str = "tutorial") -> str:
        """GET request"""
        submission = self.submission_manager.get_submission(
            "60e9612662261caad7148964", user_check=False
        )
        self.ensure_submission_custom_key(submission)
        submission = self.add_grades()
        try:
            g = submission["custom"]["coding_style"]
            grade = get_grade(g)
        except KeyError:
            self.ensure_submission_custom_key(submission)

        submission["custom"] = CodingStyleGrade(
            comments={"grade": 100, "feedback": "very good!"}
        ).dump_dict()
        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        updated = self.database.submissions.find_one_and_update(
            {"_id": submission["_id"]},
            {"$set": submission},
            return_document=ReturnDocument.AFTER,
        )
        return "This is a simple demo plugin"

    def ensure_submission_custom_key(self, submission: dict) -> dict:
        """Adds data structure for adding custom grades to a submission if it doesn't have one.

        Rationale:
        ----
        There is no formal interface for adding custom data to a submission,
        or indeed any specific structure that should be adhered to, so essentially any plugin can
        add whatever they want to the "custom" key as long as it is serializable,
        and can as a result overwrite other plugins' data with impunity.

        This method makes sure the value for the "custom" key of an INGInious submission is a dict.
        By default the value is an empty string, but if we let this value be a dict,
        multiple plugins can add data to the dict under their own key without creating conflicts."""

        if not submission.get("custom") or not isinstance(submission["custom"], dict):
            submission["custom"] = {}
        elif not isinstance(submission["custom"], dict):
            # Store original custom value under the key "original" in custom dict
            # if there already is a custom value stored there.
            submission["custom"] = {"original": submission["custom"]}
        return submission

    def add_grades(self, submission_id: str = "60e9612662261caad7148964") -> dict:
        # NOTE: A LOT OF PSEUDOCODE!

        # Get the submission
        submission = self.submission_manager.get_submission(
            submission_id, user_check=False
        )

        # Assume grades have been assigned through the web interface
        # and we receive the following data:
        data = {
            "comments": {"grade": 100, "feedback": "very good!"},
            "modularity": {"grade": 100, "feedback": "very good!"},
            "structure": {"grade": 100, "feedback": "very good!"},
            "idiomaticity": {"grade": 100, "feedback": "very good!"},
        }

        # Validate data
        grades = CodingStyleGrade(**data)

        # Make sure custom grades can be added to the submission
        submission = self.ensure_submission_custom_key(submission)

        # Add grade data
        submission["custom"]["coding_style"] = grades.dump_dict()

        updated = self.database.submissions.find_one_and_update(
            {"_id": submission["_id"]},
            {"$set": submission},
            return_document=ReturnDocument.AFTER,
        )
        return updated

    def get_submissions(self) -> None:
        # NOTE: PSEUDOCODE!
        # Demonstrates how to retrieve all submissions for a given task

        # we assume we have the course id and task id
        course_id = "tutorial"
        task_id = "04_run_student"

        # get the task we want to find submissions for
        task = self.course_factory.get_task(course_id, task_id)

        # get all submissions
        submissions = self.submission_manager.get_user_submissions(
            task
        )  # type: List[dict]

        for submission in submissions:
            # do stuff
            pass


def course_menu(course: Course, template_helper: TemplateHelper) -> Optional[str]:
    # NOTE: Just a test for adding hooks.
    # We ideally want to add a button to a submission page
    # that allows administrators to navigate to the code style
    # grading page.
    info = course.get_descriptor()
    get_logger().info("hello!")
    return template_helper.render(
        "course_menu.html", template_folder=TEMPLATES_PATH, info=info
    )


def init(
    plugin_manager: PluginManager,
    course_factory: CourseFactory,
    client: Client,
    conf: OrderedDict[str, str],
):
    """
    Allow to connect through a LDAP service

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
    plugin_manager.add_hook("course_menu", course_menu)
    plugin_manager.add_page(
        "/admin/codingstyle", CodingStyleGrading.as_view("codingstyle")
    )
