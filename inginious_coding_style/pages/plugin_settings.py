"""Implements the plugin settings page. Contains a LOT of jank due to
the way inginious_coding_style.config.PluginConfig is written."""

import typing
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from flask import request, session
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from pydantic import BaseModel, validator
from unidecode import unidecode
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.exceptions import BadRequest

from ..config import PluginConfig
from ..fs import get_config_path, update_config_file
from ..grades import GradingCategory
from ..mixins import AdminPageMixin, SubmissionMixin
from .base import BasePluginPage


class FormCategory(BaseModel):
    """Represents a new grading category from settings form."""

    name: str
    description: str
    id: str = ""  # Dynamically generated from name

    @validator("id", always=True)
    def generate_id_from_name(cls, id: str, values: Dict[str, Any]) -> str:
        name_normalized = unidecode(values["name"])
        return name_normalized.lower()


class SettingsForm(BaseModel):
    """Data structure representing keys+values of settings form."""

    config_path: Path
    weighting: float
    weighted_mean: bool = False  # checkbox needs False as default
    categories: List[FormCategory] = []  # new grading categories

    def __init__(self, **data: Any) -> None:
        to_remove = []
        categories = {}  # type: Dict[str, Dict[str, str]]
        for k, v in data.items():
            if k.startswith("new_category"):
                _, attr, id = k.rsplit("_", 2)
                categories.setdefault(id, {"name": "", "description": ""})
                categories[id][attr] = v
                to_remove.append(k)
        [data.pop(k) for k in to_remove]
        data["categories"] = [
            FormCategory(**category) for category in categories.values()
        ]
        super().__init__(**data)

    class Config:
        extra = "allow"  # why?


def update_config_with_form(config: PluginConfig, form: SettingsForm) -> PluginConfig:
    """Updates config with values from settings form.

    Parameters
    ----------
    config : PluginConfig
        The plugin's running config.
    form : SettingsForm
        Parsed values from settings form on plugin settings page.

    Returns
    -------
    PluginConfig
        Updated config
    """
    config.weighted_mean.weighting = form.weighting
    config.weighted_mean.enabled = form.weighted_mean
    # will be expanded with other settings...
    # TODO: refactor this bit:
    # # Update existing categories
    for category in config.enabled:
        description = getattr(form, f"{category}_description")  # type: str
        config.enabled[category].description = description
    # Add new categories
    config.enabled.update(
        {
            category.id: GradingCategory.parse_obj(category)
            for category in form.categories
        }
    )

    return config


class PluginSettingsPage(INGIniousAdminPage, BasePluginPage, SubmissionMixin):
    """TODO: ADD DOCSTRING"""

    def GET_AUTH(self, courseid: str) -> str:
        """Displays all coding style grades for a given course for a user."""
        course, _ = self.get_course_and_check_rights(courseid)

        config_path = get_config_path()

        return self.template_helper.render(
            "plugin_settings.html",
            template_folder=self.templates_path,
            course=course,
            user_manager=self.user_manager,
            config=self.config,
            config_path=config_path,
        )

    def POST_AUTH(self, courseid: str) -> str:
        """
        Handles a HTTP POST request dispatched from plugin settings form.

        Updates the plugin's config.

        Parameters
        ----------
        courseid: `str`
            ID of the course accessing the endpoint. (Unused)

        Returns
        -------
        `str`
            Bootstrap HTML card denoting success of operation.
        """
        self.get_course_and_check_rights(courseid)

        try:
            self._handle_update_settings(request.form)
        except Exception as e:
            self._logger.error(f"Failed to update configuration.", exc_info=e)
            return f"""<div class="alert alert-danger" role="alert">Failed to update configuration. Reason: {e}</div>"""
        else:
            return """<div class="alert alert-success" role="alert"> Successfully updated settings.</div>"""

    def _handle_update_settings(self, settings_form: ImmutableMultiDict) -> None:
        """Parses settings form and updates the config (in-memory and on-disk)
        with its values. Updates submissions in the database if weighting
        or grading mode is changed.

        Parameters
        ----------
        settings_form: `ImmutableMultiDict`
            Form data for the current request.
        """

        form = SettingsForm(**settings_form)

        # FIXME: this approach to updating the config is full of pitfalls.
        # We want to more or less perform an atomic update of the config,
        # but if we copy it, modify, then assign back to self.config, the changes
        # do not propagate throughout the program. We have to instantiate
        # some sort of singleton that is globally mutable on plugin startup.
        # The implementation below works, but could lead to a corrupt running config
        # if the update process fails mid-way.

        # Copy config so we can compare values after updating
        config_pre = deepcopy(self.config)
        update_config_with_form(self.config, form)
        update_config_file(self.config, form.config_path)

        # Recalculate all weighted mean grades if weighting is changed
        if form.weighting != config_pre.weighted_mean.weighting:
            self.recalculate_weighted_mean()

        # Swap between weighted mean grades and base grades if enabled/disabled
        if form.weighted_mean != config_pre.weighted_mean.enabled:
            self.swap_active_grade(form.weighted_mean)

        # Reset counter. See: NewCategoryEndpoint.GET_AUTH()
        session["new_category_id"] = 0

    def patch(self, courseid: str, *args, **kwargs) -> str:
        """Handles a HTTP PATCH request.

        Recalculates or repairs grades depending on URL query params.
        """
        self.get_course_and_check_rights(courseid)

        if request.args.get("recalculate") == "1":
            return self.recalculate()
        elif request.args.get("repair") == "1":
            return self.repair()
        else:
            raise BadRequest("Unknown query parameters.")

    def recalculate(self) -> str:
        """Recalculates mean grades

        Returns
        -------
        `str`
            Bootstrap HTML card denoting success of operation.
        """
        exc = None
        failed = None
        try:
            failed = self.recalculate_weighted_mean()
        except Exception as e:
            self._logger.error(
                "An exception occured when attempting to recalculate weighted mean grades of all submissions.",
                exc_info=e,
            )
            exc = e
        return self.template_helper.render(
            "recalculate_grades.html",
            template_folder=self.templates_path,
            failed=failed,
            exc=exc,
        )

    def repair(self) -> str:
        """Attempts to repair all submissions by running
        `swap_active_grade()`.

        Returns
        -------
        `str`
            Bootstrap HTML card denoting success of operation.
        """
        exc = None
        failed = None
        try:
            failed = self.swap_active_grade(self.config.weighted_mean.enabled)
        except Exception as e:
            self._logger.error(
                "An exception occured when attempting to repair submission grades.",
                exc_info=e,
            )
            exc = e

        return self.template_helper.render(
            "repair_submissions.html",
            template_folder=self.templates_path,
            failed=failed,
            exc=exc,
        )


@dataclass
class SubmissionDiagnosis:
    counter: typing.Counter[str] = field(default_factory=Counter)
    inconsistent: List[dict] = field(default_factory=list)
    missing: List[dict] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Determines if diagnostics check is passed."""
        return len(self.inconsistent) == 0 and len(self.missing) == 0


class SubmissionStatusDiagnoser(INGIniousAdminPage, BasePluginPage, AdminPageMixin):
    def GET_AUTH(self, courseid: str = None) -> str:
        # param courseid is for an eventual per-course plugin activation
        self.get_course_and_check_rights(courseid)

        diagnosis = self.diagnose_grade_consistency()

        return self.template_helper.render(
            "diagnosis.html",
            template_folder=self.templates_path,
            config=self.config,
            diagnosis=diagnosis,
        )

    def diagnose_grade_consistency(self) -> SubmissionDiagnosis:
        diag = SubmissionDiagnosis()
        target_grade = (
            "grade_mean" if self.config.weighted_mean.enabled else "grade_base"
        )

        for task in self.database.user_tasks.find():
            # Ignore user_tasks without submissions
            # (can happen if submission is deleted before it is graded)
            if not task.get("tries", 0):  # both 0 and None will skip
                continue

            grade_base = task.get("grade_base")
            grade_mean = task.get("grade_mean")
            grade = task.get("grade")
            grade_target = task.get(target_grade)

            if grade_mean is None or grade_base is None:
                diag.missing.append(task)
            elif grade_target != grade:
                diag.inconsistent.append(task)
                if grade_target == grade_base:
                    diag.counter["base"] += 1
                elif grade_target == grade_mean:
                    diag.counter["mean"] += 1
                else:
                    diag.counter["unknown"] += 1  # this should never happen

        return diag


class NewCategoryEndpoint(INGIniousAdminPage, BasePluginPage):
    def GET_AUTH(self, courseid: str, *args, **kwargs) -> str:
        self.get_course_and_check_rights(courseid)
        # TODO: Refactor. Try to do this client-side.
        id_n = session.setdefault("new_category_id", 0)
        session["new_category_id"] += 1

        return self.template_helper.render(
            "newcategory.html",
            template_folder=self.templates_path,
            id_n=id_n,
        )
