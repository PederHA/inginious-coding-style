from typing import Dict, Optional

from inginious.frontend.tasks import Task
from werkzeug.datastructures import ImmutableMultiDict

from ._types import GradesIn, INGIniousSubmission
from .submission import Submission, get_submission


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
            # NOTE: Prefer newest submission?
            best = submission
    return get_submission(best) if best else best


def has_coding_style_grades(submission: INGIniousSubmission) -> bool:
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


def parse_form_data(form_data: ImmutableMultiDict) -> GradesIn:
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
