from typing import Any, List, Optional, OrderedDict

from inginious.frontend.tasks import Task
from inginious.frontend.pages.utils import INGIniousPage

from .submission import Submission, get_submission
from .logger import get_logger


def get_submission_authors_realname(
    obj: INGIniousPage, submission: Submission
) -> List[str]:
    """Retrieves a list of the real names of a submission's authors."""
    names = []
    for username in submission.username:
        realname = obj.user_manager.get_user_realname(username)
        if realname is None:
            get_logger().debug(f"Unknown user: {username}")
            continue  # ignore unknown username
        names.append(realname)
    return names or ["Unknown"]  # fall back name


def get_submission_timestamp(submission: Submission) -> str:
    """Returns formatted timestamp of a submission's submission time."""
    s = submission.submitted_on
    return s.strftime("%Y-%m-%d %H:%M:%S") if s else "Unknown"


def get_best_submission(task: Task) -> Optional[Submission]:
    """Retrieves the best submission by a user for a specific task."""
    # HACK: we abuse the fact that a task object has access to the plugin manager here
    # in order to retrieve the submission manager. If this is changed in a future
    # version of INGInious, we will have to find a different way to do this.

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
    return get_submission(best) if best else best


def has_coding_style_grades(submission: OrderedDict[str, Any]) -> bool:
    """Checks if a submission retrieved from the INGInious submission manager
    _looks_ like it has coding style grades.

    We don't check the contents of the custom grades, we just verify that
    the submission has the correct "shape" by identifying whether or not
    `submission["custom"]["coding_style_grades"]` exists and is not empty.
    """
    try:
        return bool(submission["custom"]["coding_style_grades"])
    except:
        return False
