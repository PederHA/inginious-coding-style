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

INGInious Coding Style is highly configurable and provides granular control over which grading categories are enabled, as well as the names and descriptions of the categories.

Furthermore, experimental and cutting-edge features are made available in the `experimental` section. It is not advised to enable these settings in production. When these features are production-ready, they are moved out of the `experimental` section

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
    experimental:
      merge_grades:
        enabled: False
        weighting: 0.50
```

<!-- ## Known Issues -->

## TODO

### User Features

- [ ] Make each coding style grade progress bar on `/course/<courseid>` a clickable element that links to the relevant coding style grades page (`/submission/<submissionid>/codingstyle`) for
the relevant task.

### Plugin Configuration

- [ ] Add ability to enable/disable grading categories on a per-course basis.
- [ ] Add ability to enable/disable plugin on a per course-basis.

### Implementation Details

- [ ] Maybe we actually DON'T need to pass config to `CodingStyleGrades.get_mean()`? After all, we probably want to display the submission's mean grade at the point it was graded, not the mean grade based on the _currently_ enabled categories.

<!-- - [x] Complete -->
<!-- - [ ] Incomplete -->

## Developer Notes

This plugin uses [htmx](https://htmx.org/) to provide some interactivity.
