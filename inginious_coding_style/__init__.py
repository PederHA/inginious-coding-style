from inginious_coding_style.grades import CodingStyleGrade
from typing import Optional, OrderedDict

from inginious.client.client import Client
from inginious.frontend.course_factory import CourseFactory
from inginious.frontend.courses import Course
from inginious.frontend.pages.course_admin.submission import (
    SubmissionPage,
)  # the page we want to modify
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from inginious.frontend.plugin_manager import PluginManager
from inginious.frontend.template_helper import TemplateHelper

from pathlib import Path

from .config import PluginConfig

PLUGIN_PATH = Path(__file__).parent.absolute()
TEMPLATES_PATH = PLUGIN_PATH / "templates"


class CodingStyleGrading(INGIniousAdminPage):
    """Page to set"""

    def GET_AUTH(self, courseid: str = None):
        """GET request"""
        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        return "This is a simple demo plugin"


def course_menu(course: Course, template_helper: TemplateHelper) -> Optional[str]:
    info = course.get_descriptor()
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
            - plugin_module": "inginious-coding-style",
    *host*
        The host of the ldap server
    *encryption*
        Encryption method used to connect to the LDAP server
        Can be either "none", "ssl" or "tls"
    *request*
        Request made to the server in order to find the dn of the user. The characters "{}" will be replaced by the login name.

    """
    config = PluginConfig(**conf)
    plugin_manager.add_hook("course_menu", course_menu)
    plugin_manager.add_page(
        "/admin/codingstyle", CodingStyleGrading.as_view("codingstyle")
    )
