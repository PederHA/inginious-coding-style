# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),

## 1.4.0 (Aug 11th, 2021)

### Added

- Confirmation prompt when deleting inactive category.
- Rounding of weighted mean grade.
- Customizable task list progress bars.

## 1.3.0 (Aug 9th, 2021)

### Added

- Button to delete coding style grades from a submission.

### Fixed

- Permission checking for admin-only pages.
    - Prior to this version, students could edit their own (but not other's) submissions' coding style grades. (oops)

### Changed

- Refactored submission, course and task retrieval for `INGIniousPage` subclasses. They now share a common interface for retrieving these.

## 1.2.0 (Aug 8th, 2021)

### Added

- Submission query page hooks.
    - Coding style grade status column to submission query page.
    - Coding style grading button to submission query page.
    - `submission_query` config section.
- Weighted mean grade calculation.
    - Based on the previous `merge_grades` functionality, but now lets administrators define a custom weight for coding style grades used to find the weighted mean.
    - Option to show separate bars for automated correctness grade given by INGInious and coding style grade ([`task_list_bar`](https://pederha.github.io/inginious-coding-style/configuration/#task_list_bar)).

### Changed

- `merge_grades` config section has been renamed to `weighted_mean`.

### Removed

- `experimental` section in config.

## 1.1.1 (Aug 3rd, 2021)

### Fixed

- Attempting to remove an inactive category raising an exception due to not using the new Pydantic Submission model.

- Student grades page navbar breadcrumb.

## 1.1.0 (Aug 3rd, 2021)

### Added

- Shared exception handling functionality for subclasses of `INGIniousPage`.

- Exception handler for `ValidationError` exceptions. Currently logs the exception and displays Internal Server Error in the browser.

### Changed

- Submissions are now validated with Pydantic. This makes it easier to reason with the code, as there is now a distinction between a raw submission returned by the INGInious `SubmissionManager` and a submission that has been parsed by the plugin and been assigned a `CodingStyleGrades` object.

## 1.0.2 (Aug 1st, 2021)

### Added
- Mean grade to sidebar of grades page (admin+student).
- Tooltip to button for removing disabled category from a submission.

### Changed
- Elements on grades page (admin+student) should line up more evenly now.


### Fixed
- Incorrect rendering of grades page (admin+student) when an odd number of grading categories are enabled.
- Removing a disabled category from submission on grades page (admin) always raising a `TypeError` exception.

## 1.0.1 (July 29th, 2021)

### Added
- README to PyPi build.

### Fixed
- Include up-to-date version of `pyproject.toml`.

## 1.0.0 (July 29th, 2021)

Initial release.
