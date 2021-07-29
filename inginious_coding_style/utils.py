from typing import Optional, TYPE_CHECKING

from inginious.frontend.tasks import Task

from ._types import Submission, HasUserManager

if TYPE_CHECKING:
    from datetime import datetime


def get_user_realname(obj: HasUserManager, submission: Submission) -> str:
    """Retrieves the real name of the author of a submission."""
    # TODO: handle group submissions
    user_realname = None
    try:
        user_realname = obj.user_manager.get_user_realname(submission["username"][0])
    except (IndexError, KeyError):
        obj._logger.error(f"Unable to get username for submission {submission}.")
    return user_realname or "Unknown user"


def get_submission_timestamp(submission: Submission) -> str:
    """Returns formatted timestamp of a submission's submission time."""
    s = submission.get("submitted_on")  # type: Optional[datetime]
    return s.strftime("%Y-%m-%d %H:%M:%S") if s else "Unknown"


def has_coding_style_grades(submission: Submission, plugin_key: str) -> bool:
    """Determines if a Submission object looks like it contains coding style grades.

    NOTE: This function only verifies that _something_ is present at `Submission["custom"][PLUGIN_KEY]`.
    The actual contents are not verified. `.grades.get_grades()` handles the
    verification of the contents.
    """
    # TODO: merge this function with get_grades or something?
    return (
        bool(submission.get("custom"))
        and isinstance(submission["custom"], dict)
        and submission["custom"].get(plugin_key)
    )


def get_best_submission(task: Task) -> Optional[Submission]:
    """Retrieves the best submission by a user for a specific task."""
    # Check if we can find any submissions at all
    submission_manager = task._plugin_manager.get_submission_manager()
    submissions = submission_manager.get_user_submissions(task)
    if not submissions:
        return None

    # We have submissions, now find the best one
    best = None
    for submission in submissions:
        if best is None or submission["grade"] > best["grade"]:
            best = submission
    return best
