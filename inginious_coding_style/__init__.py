from pathlib import Path
from typing import Any, List, OrderedDict, Tuple, Union

from inginious.client.client import Client
from inginious.frontend.course_factory import CourseFactory
from inginious.frontend.courses import Course
from inginious.frontend.plugin_manager import PluginManager
from inginious.frontend.tasks import Task
from inginious.frontend.template_helper import TemplateHelper

from ._types import INGIniousSubmission
from .config import PluginConfig, get_config
from .pages import (CodingStyleGradingPage, FixConfigPermissionsEndpoint,
                    NewCategoryEndpoint, PluginSettingsPage,
                    StudentSubmissionCodingStylePage,
                    SubmissionStatusDiagnoser)
from .utils import get_best_submission, has_coding_style_grades

__version__ = "1.5.1"

PLUGIN_PATH = Path(__file__).parent.absolute()
TEMPLATES_PATH = PLUGIN_PATH / "templates"

# Makes plugin config available globally
PLUGIN_CONFIG: PluginConfig = None  # type: ignore


def submission_admin_menu(
    course: Course,
    task: Task,
    submission: INGIniousSubmission,
    template_helper: TemplateHelper,
) -> str:
    return template_helper.render(
        "submission_admin_menu.html",
        template_folder=TEMPLATES_PATH,
        submission=submission,
    )


# TODO: add *args, **kwargs to all plugin hook functions to accomodate future additions to hook parameters


def submission_query_header(
    course: Course,
    template_helper: TemplateHelper,
) -> str:
    return template_helper.render(
        "submission_query_header.html",
        config=PLUGIN_CONFIG,
        template_folder=TEMPLATES_PATH,
    )


def submission_query_cell(
    course: Course,
    submission: INGIniousSubmission,
    template_helper: TemplateHelper,
) -> str:
    return template_helper.render(
        "submission_query_cell.html",
        has_grades=has_coding_style_grades(submission),
        submission=submission,
        template_folder=TEMPLATES_PATH,
    )


def submission_query_button(
    course: Course,
    submission: INGIniousSubmission,
    template_helper: TemplateHelper,
) -> str:
    # TODO: in the future, we should attempt to cache submission info
    # so that we don't have to do twice the amount of work for two hooks.
    if not PLUGIN_CONFIG.submission_query.button:
        return ""
    return template_helper.render(
        "submission_query_button.html",
        has_grades=has_coding_style_grades(submission),
        submission=submission,
        template_folder=TEMPLATES_PATH,
    )


def task_list_item(
    course: Course,
    task: Task,
    tasks_data: Any,
    template_helper: TemplateHelper,
) -> str:
    """Displays a progress bar denoting the current coding style grade
    for a given task."""
    # TODO: optimize. Cache best submission?
    submission = get_best_submission(task)
    if not submission or not submission.custom.coding_style_grades:
        return ""

    return template_helper.render(
        "task_list_item.html",
        template_folder=TEMPLATES_PATH,
        style_grade=submission.custom.coding_style_grades.get_mean(PLUGIN_CONFIG),
        submission=submission,
        config=PLUGIN_CONFIG,
    )


def task_list_bar_label(course: Course, template_helper: TemplateHelper) -> str:
    """Modifies the label for the default INGInious grade progress bar."""
    if not PLUGIN_CONFIG.task_list_bars.total_grade.enabled:
        return ""
    return PLUGIN_CONFIG.task_list_bars.total_grade.label


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


def course_admin_menu(course: Course, *args, **kwargs) -> Tuple[str, str]:
    """Adds link to admin menu for plugin configuration"""
    # TODO: If plugin can be enabled/disabled per-course
    #       this func should return HTML or None depending on configuration
    return ("settings/codingstyle", '<i class="fa fa-star"></i> Coding Style settings')


def init(
    plugin_manager: PluginManager,
    course_factory: CourseFactory,
    client: Client,
    conf: OrderedDict[str, Union[str, List[str]]],
):
    """
    Allows teachers to grade several aspect of a student submission's code style.

    Available configuration:
    https://pederha.github.io/inginious-coding-style/configuration/
    """
    # Get config and make it global
    config = get_config(conf)
    global PLUGIN_CONFIG
    PLUGIN_CONFIG = config

    #############################
    #                           #
    #           HOOKS           #
    #                           #
    #############################

    # Add label to default INGInious grade progress bars
    plugin_manager.add_hook("task_list_bar_label", task_list_bar_label)

    # Display coding style grades in list of tasks for a course
    plugin_manager.add_hook("task_list_item", task_list_item)

    # Show button to navigate to detailed coding style grades for a submission
    plugin_manager.add_hook("task_menu", task_menu)

    # Show button to navigate to coding style grading page for admins
    plugin_manager.add_hook("submission_admin_menu", submission_admin_menu)

    # Show button to navigate to coding style grading page for admins
    plugin_manager.add_hook("course_admin_menu", course_admin_menu)

    # Add header to submission query table
    plugin_manager.add_hook(
        "submission_query_header",
        submission_query_header,
        prio=config.submission_query.priority,
    )

    # Add column to submission query table
    plugin_manager.add_hook(
        "submission_query_cell",
        submission_query_cell,
        prio=config.submission_query.priority,
    )

    # Add button to submission query table row
    plugin_manager.add_hook(
        "submission_query_button",
        submission_query_button,
        prio=config.submission_query.priority,
    )

    #############################
    #                           #
    #           PAGES           #
    #                           #
    #############################

    # Grading interface for admins
    plugin_manager.add_page(
        "/admin/codingstyle/submission/<submissionid>",
        CodingStyleGradingPage.as_view(
            "codingstyle_grading",
            config,
            TEMPLATES_PATH,
        ),
    )

    # Coding Style Grade view for a specific user submission
    plugin_manager.add_page(
        "/submission/<submissionid>/codingstyle",
        StudentSubmissionCodingStylePage.as_view(
            "codingstyle_submission",
            config,
            TEMPLATES_PATH,
        ),
    )

    # Plugin configuration
    plugin_manager.add_page(
        "/admin/<courseid>/settings/codingstyle",
        PluginSettingsPage.as_view(
            "codingstyle_settings",
            config,
            TEMPLATES_PATH,
        ),
    )

    plugin_manager.add_page(
        "/admin/<courseid>/settings/codingstyle/diagnose",
        SubmissionStatusDiagnoser.as_view(
            "submission_status_diagnoser",
            config,
            TEMPLATES_PATH,
        ),
    )

    plugin_manager.add_page(
        "/admin/<courseid>/settings/codingstyle/category",
        NewCategoryEndpoint.as_view(
            "new_category_endpoint",
            config,
            TEMPLATES_PATH,
        ),
    )

    plugin_manager.add_page(
        "/admin/<courseid>/settings/codingstyle/fixconfig",
        FixConfigPermissionsEndpoint.as_view(
            "fix_config_permissions_endpoint",
            config,
            TEMPLATES_PATH,
        ),
    )
