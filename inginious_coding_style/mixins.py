from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, cast

from bson.errors import InvalidId
from inginious.frontend.courses import Course
from inginious.frontend.pages.utils import INGIniousPage
from inginious.frontend.tasks import Task
from werkzeug.exceptions import Forbidden, InternalServerError, NotFound

from ._types import GradesIn, INGIniousUserTask, PluginUserTask
from .config import PluginConfig
from .grades import get_grades
from .submission import Submission, get_submission


@dataclass
class SubmissionMetadata:
    """Contains human-readable submission metadata."""

    authors: List[str]
    graded_by: List[str]
    submitted_on: str


class BaseMixin(INGIniousPage):
    config: PluginConfig


class SubmissionMixin(BaseMixin):
    """This mixin class provides a common interface for working with
    submissions for _any_ class that inherits from
    `inginious.frontend.pages.utils.INGIniousPage`.

    `inginious.frontend.pages.course_admin.SubmissionPage` is an
    admin-only page, and therefore classes that implement pages that should
    be accessible to normal users are unable inherit from it (?).
    Therefore, we must implement our own interface for retrieving
    submissions that can be used by any `INGIniousPage` subclass.
    """

    def get_submission(
        self,
        submissionid: str,
        user_check: bool = False,
    ) -> Tuple[Course, Task, Submission]:
        """Alternative implementation of INGInious's
        `SubmissionPage.fetch_submission`, that provides more robust
        exception handling, checks user privileges, as well as returning
        a `Submission` instead of an `INGIniousSubmission`."""
        submission = self._fetch_submission(submissionid, user_check)
        course = self._fetch_course(submission)
        task = self._fetch_task(submission, course)
        return course, task, submission

    def get_user_realnames(self, usernames: List[str]) -> List[str]:
        """Retrieves a list of the real names from a list of INGInious usernames."""
        names = []
        for username in usernames:
            realname = self.user_manager.get_user_realname(username)
            if realname is not None:
                names.append(realname)
            else:
                names.append(username)
                self._logger.debug(f"Unknown user: {username}")
        return names

    def get_submission_authors_realname(
        self, submission: Submission, default: str = "Unknown"
    ) -> List[str]:
        """Wrapper around get_user_realnames() that falls back on a
        default username if submission has no authors associated with it."""
        return self.get_user_realnames(submission.username) or [default]

    def get_submission_metadata(self, submission: Submission) -> SubmissionMetadata:
        """Creates a datastructure containing submission metadata formatted
        to be human-readable."""
        return SubmissionMetadata(
            authors=self.get_submission_authors_realname(submission),
            graded_by=self.get_user_realnames(submission.custom.graded_by),
            submitted_on=submission.get_timestamp(),
        )

    def _fetch_submission(self, submissionid: str, user_check: bool) -> Submission:
        """Slimmed down version of SubmissionPage.fetch_submission.
        Only returns Submission, instead of Tuple[Course, Task, OrderedDict].

        TODO: should submissionid be of type `ObjectId`?
        """
        try:
            submission = self.submission_manager.get_submission(
                submissionid, user_check
            )
            if not submission:
                raise NotFound(description=_("This submission doesn't exist."))
        except InvalidId as ex:
            self._logger.info("Invalid ObjectId : %s", submissionid)
            raise Forbidden(description=_("Invalid ObjectId."))
        return get_submission(submission)

    def _fetch_course(
        self,
        submission: Submission,
    ) -> Course:
        """Retrieves a course for a given submission."""
        try:
            course = self.course_factory.get_course(submission.courseid)
        except Exception as e:
            if not submission.courseid:
                msg = (
                    f"Submission {submission._id} is not associated with any course. "
                    "Has the submission been corrupted?"
                )
            else:
                msg = (
                    f"Unable to find course with course ID {submission.courseid}. "
                    "Has it been deleted?"
                )
            self._logger.error(msg)
            raise InternalServerError("Unable to display submission.")
        return course

    def _fetch_task(self, submission: Submission, course: Course) -> Task:
        """Retrieves a task for a given submission and course."""
        try:
            task = course.get_task(submission.taskid)
        except Exception as e:
            if not submission.taskid:  # 2021-11-23: I think this should be NOT
                msg = (
                    f"Submission {submission._id} is not associated with a task. "
                    "Has the submission been corrupted?"
                )
            else:
                msg = (
                    f"Unable to find task with task ID {submission.taskid}. "
                    "Has it been deleted?"
                )
            self._logger.error(msg)
            raise InternalServerError("Unable to display submission.")
        return task

    def swap_active_grade(self, to_mean: bool) -> List[INGIniousUserTask]:
        """Enables/disables weighted grades for all top submissions by
        modifying the `grade` key of each submission stored in the
        `user_tasks` collection.

        Parameters
        ----------
        to_mean : `bool`, optional
            Whether to swap grades to weighted mean grades or to
            INGInious base grades.

        Returns
        -------
        `List[dict]`
            Submissions that could not be modified.
        """
        failed: List[INGIniousUserTask] = []
        for user_task in self.database.user_tasks.find():  # type: INGIniousUserTask
            try:
                # Skip user tasks with 0 student attempts
                if user_task.get("tried", 0) == 0:
                    continue
                task = self._check_and_fix_user_task(user_task)

                if to_mean:  # Set active grade to either BASE or MEAN
                    task["grade"] = task["grade_mean"]
                else:
                    task["grade"] = task["grade_base"]

                self.database.user_tasks.update_one(  # Update item in database
                    # NOTE: is it faster to pass {"$set": {"grade": active_grade}}
                    #       as the `update` argument?
                    {"_id": task["_id"]},
                    {"$set": task},
                )
            except Exception as e:
                self._logger.error(
                    f"Failed to modify submission {task.get('submissionid')}",
                    exc_info=e,
                )
                failed.append(user_task)
        return failed

    def recalculate_weighted_mean(self) -> List[INGIniousUserTask]:
        """Recalculates weighted mean grades for all documents in the
        `user_tasks` collection.

        Returns
        -------
        `List[dict]`
            Submissions that failed to be modified.
        """
        failed: List[INGIniousUserTask] = []
        for user_task in self.database.user_tasks.find():  # type: INGIniousUserTask
            try:
                # Skip user tasks with 0 tries
                if user_task.get("tried", 0) == 0:
                    continue
                task = self._check_and_fix_user_task(user_task)
                submission = self._fetch_submission(
                    task.get("submissionid", "0"), user_check=False
                )  # FIXME: check if we should default to ObjectId instead of str
                self.set_user_tasks_grades(submission)
            except Exception as e:
                self._logger.error(
                    f"Failed to modify submission {user_task.get('submissionid')}",
                    exc_info=e,
                )
                failed.append(user_task)
        return failed

    def _check_and_fix_user_task(self, user_task: INGIniousUserTask) -> PluginUserTask:
        """Ensures a document from the `user_tasks` collection contains
        the keys required to modify its displayed grade on the frontend.
        If the document does not have the keys `grade_base` and/or
        `grade_mean`, they are calculated and added to the document.

        Parameters
        ----------
        user_task : INGIniousUserTask
            A document from the `user_tasks` DB collection

        Returns
        -------
        PluginUserTask
            Modified `user_tasks` document that includes keys/values
            required by the plugin.

        Raises
        ------
        `KeyError`
            Raised if `user_task` has no grade. The usual
            exceptions raised by `_fetch_submission()` also apply. Callers of
            this method should implement exception handling accordingly.
        """
        for key in ["grade", "submissionid"]:
            if user_task.get(key) is None:
                raise KeyError(f"User Task {user_task.get('_id')} has no key '{key}'.")

        # mypy: Signal that our user task has the correct type
        # FIXME: This will cause issues if we expand PluginUserTask in the future
        user_task = cast(PluginUserTask, user_task)

        if user_task.get("grade_base") is None or user_task.get("grade_mean") is None:
            # Fetch submission and set user_task's grade_base to submission's grade
            submission = self._fetch_submission(
                user_task["submissionid"],
                user_check=False,
            )
            # Check for base grade
            if user_task.get("grade_base") is None:
                user_task["grade_base"] = submission.grade

            # Check for weighted mean grade
            if user_task.get("grade_mean") is None:
                user_task["grade_mean"] = submission.get_weighted_mean(self.config)

        return user_task

    def remove_category_from_submission(
        self, submission: Submission, category: str
    ) -> None:
        """Removes a grading category from a submission.
        Does nothing if submission does not have a category with that name.

        Parameters
        ----------
        submission : `Submission`
            The submission to modify.
        category : `str`
            Name of the category to remove.
        """
        submission.custom.coding_style_grades.remove_category(category)
        self.update_submission(submission)

    def update_submission_grades(
        self, submission: Submission, grades_data: GradesIn
    ) -> None:
        """Attempts to update a submission with a new set of coding style grades.

        Raises `ValidationError` if grades cannot be validated.

        Parameters
        ----------
        submission : `Submission`
            The submission to update grades of.
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
        #   * Retrieve a copy of the currently enabled categories from
        #     the config (self.config.dict()["enabled"])
        #   * Iterate through the grade data from the webapp form (grades_data)
        #   * Update each enabled grade with data from the webapp form
        #   * Add the new grades to the submission for each category
        #     (overwriting the old grades)
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

        # Add session username to submission's list of tutors who have graded it
        username = self.user_manager.session_username()
        if not username:
            self._logger.warning(
                f"Unable to get session username when grading submission {submission._id}. "
                f"SessionID: {self.user_manager.session_id}"
            )
        elif username and username not in submission.custom.graded_by:
            submission.custom.graded_by.append(username)

        self.update_submission(submission)

    def update_submission(self, submission: Submission) -> None:
        """Finds an existing submission and updates it with new data."""
        # TODO: Wrap these two operations in a transaction somehow?
        self.set_user_tasks_grades(submission)
        self.database.submissions.update_one(
            {"_id": submission._id},
            {"$set": submission.dict()},
        )

    def set_user_tasks_grades(self, submission: Submission) -> None:
        """
        Finds the weighted mean of a submission's base grade and coding
        style grades, and updates its document in the DB collection
        'user_tasks' with updated grade, which is a collection that holds
        top submissions for every user for each task.

        The submission's  base grade and weighted grade are stored
        separately under the keys `grade_base` and `grade_mean` while the
        value of the original `grade` key is set to either base grade or
        mean grade depending on the active configuration.

        Weighted mean grade is always calculated, but the `grade` attribute
        will only be set to the weighted mean grade if weighted mean grading
        is enabled.

        NOTE: This method has no effect if the submission that is being
        graded is _not_ the user's top submission for the given task.
        This is due to the way INGInious seems to store a sort of
        "meta-submission" in the 'user_tasks' collection, which keeps
        track of the user's best grade for a specific task and the number
        of submissions they have made for that task, and the ID of their
        top submission. It is that grade that is displayed on the course's
        task list, and thus it is also the one we are modifying in this method.
        Furthermore, it makes no sense to grade a submission that ISN'T
        the user's best submission, so that is also relevant!
        """
        grade_base = submission.grade
        grade_mean = submission.get_weighted_mean(self.config)
        grade = grade_mean if self.config.weighted_mean.enabled else grade_base

        # Update the 'user_tasks' collection (where top submissions are stored)
        self.database.user_tasks.find_one_and_update(
            {"submissionid": submission._id},
            {
                "$set": {
                    "grade": grade,  # the active grade
                    "grade_mean": grade_mean,
                    "grade_base": grade_base,
                }
            },
        )


class AdminPageMixin(BaseMixin):
    def check_course_privileges(self, course: Course, allow_staff: bool = True) -> None:
        """Checks if a user has admin or staff privileges on a course.
        Raises a `Forbidden` exception if lacking rights.

        Basically INGIniousAdminPage.get_course_and_check_rights() except
        we already have the course, and just want to check privileges.
        """
        if allow_staff:
            func = self.user_manager.has_staff_rights_on_course
        else:
            func = self.user_manager.has_admin_rights_on_course
        has_priv = func(course)
        if has_priv:
            return  # we have privileges

        if allow_staff:
            raise Forbidden(
                description=_("You don't have staff rights on this course.")
            )
        else:
            raise Forbidden(
                description=_("You don't have admin rights on this course.")
            )
