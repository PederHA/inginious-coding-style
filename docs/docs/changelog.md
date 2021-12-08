# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.1] 2021-12-08

### Added

- Detection and repair of config that cannot be written to by inginious-webapp.
    - Now shows an alert and button that can be pressed to attempt to make the configuration file writable.

## [1.5.0] 2021-12-05

### Added

- `graded_by` attribute for submissions which keeps track of which tutors/admins have graded a submission. This change is reflected on the front-end as well.
- Option to show/hide the `graded_by` info in the sidebar of student coding style grades overview (`/submissions/<submissionid>/codingstyle`).
- Plugin configuration menu in the INGInious WebApp which can be located in the sidebar of the administration page of any course (`/admin/<courseid>/settings`).

### Changed

- All references to "correctness" have been replaced by "completion".

## [1.4.0] - 2021-08-11

### Added

- Confirmation prompt when deleting inactive category.
- Rounding of weighted mean grade.
- Customizable task list progress bars.

## [1.3.0] - 2021-08-09

### Added

- Button to delete coding style grades from a submission.

### Fixed

- Permission checking for admin-only pages.
    - Prior to this version, students could edit their own (but not other's) submissions' coding style grades. (oops)

### Changed

- Refactored submission, course and task retrieval for `INGIniousPage` subclasses. They now share a common interface for retrieving these.

## [1.2.0] - 2021-08-08

### Added

- Submission query page hooks.
    - Coding style grade status column to submission query page.
    - Coding style grading button to submission query page.
    - `submission_query` config section.
- Weighted mean grade calculation.
    - Based on the previous `merge_grades` functionality, but now lets administrators define a custom weight for coding style grades used to find the weighted mean.
    - Option to show separate bars for automated completion grade given by INGInious and coding style grade ([`task_list_bar`](https://pederha.github.io/inginious-coding-style/configuration/#task_list_bar)).

### Changed

- `merge_grades` config section has been renamed to `weighted_mean`.

### Removed

- `experimental` section in config.

## [1.1.1] - 2021-08-03

### Fixed

- Attempting to remove an inactive category raising an exception due to not using the new Pydantic Submission model.

- Student grades page navbar breadcrumb.

## [1.1.0] - 2021-08-03

### Added

- Shared exception handling functionality for subclasses of `INGIniousPage`.

- Exception handler for `ValidationError` exceptions. Currently logs the exception and displays Internal Server Error in the browser.

### Changed

- Submissions are now validated with Pydantic. This makes it easier to reason with the code, as there is now a distinction between a raw submission returned by the INGInious `SubmissionManager` and a submission that has been parsed by the plugin and been assigned a `CodingStyleGrades` object.

## [1.0.2] 2021-08-01

### Added
- Mean grade to sidebar of grades page (admin+student).
- Tooltip to button for removing disabled category from a submission.

### Changed
- Elements on grades page (admin+student) should line up more evenly now.


### Fixed
- Incorrect rendering of grades page (admin+student) when an odd number of grading categories are enabled.
- Removing a disabled category from submission on grades page (admin) always raising a `TypeError` exception.

## [1.0.1] 2021-07-29

### Added
- README to PyPi build.

### Fixed
- Include up-to-date version of `pyproject.toml`.

## [1.0.0] 2021-07-29

Initial release.
