# INGInious Coding Style

INGInious Coding Style is a plugin for INGInious 0.7 and up that allows tutors to grade several aspect of student submissions' coding style.

INGInious Coding Style should be easy to use for both tutors and students. The plugin adds new buttons and elements to various existing menus in the application that can be used to add and view coding style grades.

## Documentation

Full documentation can be found here: https://pederha.github.io/inginious-coding-style/

## Installation

```bash
pip install inginious-coding-style
```

## Configuration

INGInious Coding Style is highly configurable and provides granular control of the majority of its features. Despite this, extensive configuration is not necessary, as the plugin tries to implement sensible defaults, and therefore should just work straight out of the box.

### Minimal Configuration

The following YAML snippet provides the default plugin configuration, and is a good starting point for exploring the plugin's functionality:

```yml
plugins:
-   plugin_module: inginious_coding_style
    name: "INGInious Coding Style"
```

### Full Configuration

Below is an example of a configuration making use of all available configuration options.

```yml
plugins:
-   plugin_module: inginious_coding_style
    name: "INGInious Coding Style"
    enabled:
        # This enables all default categories + 1 custom category
        - comments
        - modularity
        - structure
        - idiomaticity
        - coolness # Our custom category
    categories:
        # This is a definition for a new category
      - id: coolness
        name: Coolness
        description: How cool the code looks B-)
      # This redefines a default category
      - id: comments
        name: Kommentering
        description: Hvor godt kommentert koden er.
    submission_query:
        header: CSG
        button: true
        priority: 3000
    weighted_mean:
        enabled: false
        weighting: 0.25
        task_list_bar: true
```

<!-- ## Known Issues -->

## TODO

### User Features

- [ ] Make each coding style grade progress bar on `/course/<courseid>` a clickable element that links to the relevant coding style grades page (`/submission/<submissionid>/codingstyle`) for
the relevant task.

### Admin/Tutor Features

- [ ] Add `graded_by: List[str]` attribute to `CodingStyleGrades` to record which admin/tutor graded the submission's coding style.

### Plugin Configuration

- [ ] Add ability to enable/disable grading categories on a per-course basis.
- [ ] Add ability to enable/disable plugin on a per course-basis.

### Robustness

- [ ] Better exception handling for Pydantic `ValidationError`. If something fails to validate, we should be able to display human-readable messages both in the web interface and in the logs.

<!-- - [x] Complete -->
<!-- - [ ] Incomplete -->

## Developer Notes

This plugin uses [htmx](https://htmx.org/) to provide some interactivity.
