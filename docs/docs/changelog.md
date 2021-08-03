# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),

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
