from logging import Logger
from typing import List, Tuple

from bson.errors import InvalidId
from inginious.frontend.course_factory import CourseFactory
from inginious.frontend.courses import Course
from inginious.frontend.submission_manager import WebAppSubmissionManager
from inginious.frontend.tasks import Task
from inginious.frontend.user_manager import UserManager
from werkzeug.exceptions import Forbidden, InternalServerError, NotFound

from .submission import Submission, get_submission


class BaseMixin:
    _logger: Logger
    submission_manager: WebAppSubmissionManager
    user_manager: UserManager
    course_factory: CourseFactory


class SubmissionMixin(BaseMixin):
    """This mixin class provides a common interface for working with submissions for _any_
    class that inherits from `inginious.frontend.pages.utils.INGIniousPage`

    `inginious.frontend.pages.course_admin.SubmissionPage` is an admin-only page,
    and therefore classes that implement pages that are accessible to normal users
    are unable inherit from it (?). Therefore, we must implement our own interface
    for retrieving submissions that can be used by any `INGIniousPage` subclass.
    """

    def get_submission(
        self,
        submissionid: str,
        user_check: bool = False,
    ) -> Tuple[Course, Task, Submission]:
        """Alternative implementation of INGInious's
        `SubmissionPage.fetch_submission`, that provides more robust
        exception handling, checks user privileges, as well as returning
        the submission as a `Submission` object."""
        submission = self._fetch_submission(submissionid, user_check)
        course = self._fetch_course(submission)
        task = self._fetch_task(submission, course)
        return course, task, submission

    def get_submission_authors_realname(self, submission: Submission) -> List[str]:
        """Retrieves a list of the real names of a submission's authors."""
        names = []
        for username in submission.username:
            realname = self.user_manager.get_user_realname(username)
            if realname is None:
                self._logger.debug(f"Unknown user: {username}")
                continue  # ignore unknown username
            names.append(realname)
        return names or ["Unknown"]  # fall back name

    def _fetch_submission(self, submissionid: str, user_check: bool) -> Submission:
        """Slimmed down version of SubmissionPage.fetch_submission.
        Only returns Submission, instead of Tuple[Course, Task, OrderedDict]"""
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
        try:
            task = course.get_task(submission.taskid)
        except Exception as e:
            if not submission.taskid:
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


class AdminPageMixin(BaseMixin):
    """This one's a little questionable in design, but exists
    to avoid having to retrieve a course twice just to check permissions."""

    def has_course_privileges(self, course: Course, allow_staff: bool) -> bool:
        if allow_staff:
            return self.user_manager.has_staff_rights_on_course(course)
        else:
            return self.user_manager.has_admin_rights_on_course(course)

    def do_check_course_privileges(
        self, course: Course, allow_staff: bool = True
    ) -> None:
        """Checks if a user has admin or staff privileges on a course.
        Raises a 403 Forbidden exception if lacking rights."""
        has_priv = self.has_course_privileges(course, allow_staff)
        if has_priv:
            return

        # NOTE: Lifted straight from INGIniousAdminPage.get_course_and_check_rights
        if allow_staff:
            if not self.user_manager.has_staff_rights_on_course(course):
                raise Forbidden(
                    description=_("You don't have staff rights on this course.")
                )
        else:
            if not self.user_manager.has_admin_rights_on_course(course):
                raise Forbidden(
                    description=_("You don't have admin rights on this course.")
                )
