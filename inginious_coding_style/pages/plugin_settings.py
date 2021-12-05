"""Implements the plugin settings page. Contains a LOT of jank due to
the way inginious_coding_style.config.PluginConfig is written.

Alternative name: 'Technical Debt: The Module'
"""

import typing
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from flask import request, session
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from pydantic import BaseModel, validator
from unidecode import unidecode
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.exceptions import BadRequest

from .._types import INGIniousUserTask
from ..config import PluginConfig, SubmissionQuerySettings, TaskListBars
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
    categories: Dict[str, GradingCategory]  # new grading categories
    task_list_bars: TaskListBars
    show_graders: bool = False
    submission_query: SubmissionQuerySettings


class FormParser:
    """Parses the plugin settings form."""

    form: Dict[str, Any]

    def __init__(self, form: ImmutableMultiDict, config: PluginConfig) -> None:
        self.form = form.to_dict()
        self.config = config

    def parse(self) -> SettingsForm:
        categories = self.parse_categories()
        task_list_bars = self.parse_task_list_bars()
        submission_query = self.parse_submission_query()
        return SettingsForm(
            config_path=self.form["config_path"],
            weighting=self.form["weighting"],
            weighted_mean=self.form.get("weighted_mean", False),
            categories=categories,
            task_list_bars=task_list_bars,
            show_graders=self.form.get("show_graders", False),  # checkbox default
            submission_query=submission_query,
        )

    def parse_categories(self) -> Dict[str, GradingCategory]:
        categories = self.get_existing_categories()
        new_categories = self.get_new_categories()
        categories.update(new_categories)
        return categories

    def get_existing_categories(self) -> Dict[str, GradingCategory]:
        """Updates existing categories and deletes categories from
        the config that have been removed via the settings form."""
        # set that keeps track of which categories are present in form
        # Categories that are absent from this set are removed from the config
        enabled = set()  # type: Set[str]

        categories = deepcopy(self.config.enabled)
        for k, v in self.form.items():
            if k.startswith("category"):
                _, attr, id = k.split("_", 2)
                setattr(categories[id], attr, v)
                enabled.add(id)

        # Only return enabled categories (don't return removed categories)
        return {k: v for k, v in categories.items() if k in enabled}

    def get_new_categories(self) -> Dict[str, GradingCategory]:
        categories = {}  # type: Dict[str, Dict[str, str]]
        for k, v in self.form.items():
            if k.startswith("new_category"):
                _, attr, id = k.rsplit("_", 2)  # new_category, name/description, <N>
                categories.setdefault(
                    id,
                    {
                        "id": "",
                        "name": "",
                        "description": "",
                    },
                )
                categories[id][attr] = v

        # Create an id for the new category based on its name
        for category in categories.values():
            if category["id"] == "":
                # TODO: handle missing name
                category["id"] = unidecode(category["name"]).lower()

        return {
            category["id"]: GradingCategory(**category)
            for category in categories.values()
        }

    def parse_task_list_bars(self) -> TaskListBars:
        b = [(k, v) for k, v in self.form.items() if k.startswith("bar")]
        bars = {}  # type: Dict[str, Dict[str, Union[str, bool]]]
        for k, v in b:
            _, attr, bar_type = k.split("_", 2)
            bars.setdefault(bar_type, {})
            bars[bar_type][attr] = v

        # Set enabled to false where "enabled" attr is missing
        for k, v in bars.items():
            if not v.get("enabled"):
                v["enabled"] = False  # Form returns nothing if box is unchecked

        return TaskListBars(**bars)

    def parse_submission_query(self) -> SubmissionQuerySettings:
        s = [(k, v) for k, v in self.form.items() if k.startswith("submissionquery")]
        d = {}  # type: Dict[str, Union[str, int, bool]]
        for k, v in s:
            _, attr = k.split("_", 1)
            d[attr] = v
        if not d.get("button"):
            d["button"] = False
        return SubmissionQuerySettings(**d)


def parse_settings_form(form: ImmutableMultiDict, config: PluginConfig) -> SettingsForm:
    p = FormParser(form, config)
    return p.parse()


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
    # TODO: Make this process automatic with some metaprogramming magic
    #       There are way too many functional dependencies being introduced
    #       in this module already.
    config.weighted_mean.weighting = form.weighting
    config.weighted_mean.enabled = form.weighted_mean
    config.enabled = form.categories
    config.task_list_bars = form.task_list_bars
    config.show_graders = form.show_graders
    config.submission_query = form.submission_query
    return config


class PluginSettingsPage(INGIniousAdminPage, BasePluginPage, SubmissionMixin):
    """Page that displays plugin settings and submission diagnostics."""

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
            return """
                <div
                    class="alert alert-success update-success"
                    _="on load wait 5s then transition opacity to 0 then remove me"
                    role="alert"
                >
                    Successfully updated settings.
            </div>
            """

    def _handle_update_settings(self, settings_form: ImmutableMultiDict) -> None:
        """Parses settings form and updates the config (in memory and on disk)
        with its values. Updates submissions in the database if weighting
        or grading mode is changed.

        Parameters
        ----------
        settings_form: `ImmutableMultiDict`
            Form data for the current request.
        """

        form = parse_settings_form(settings_form, self.config)

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
        exc: Optional[Exception] = None
        failed: List[INGIniousUserTask] = []
        try:
            failed = self.swap_active_grade(self.config.weighted_mean.enabled)
        except Exception as exc:
            self._logger.error(
                "An exception occured when attempting to repair submission grades.",
                exc_info=exc,
            )

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
    """Attempts to diagnose broken coding style grades for all submissions."""

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
