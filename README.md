# INGInious Coding Style Grader

A plugin for INGInious that allows tutors to grade several aspect of student submissions' coding style.

## Installation

```bash
pip install inginious-coding-style
```

## Configuration

INGInious Coding Style is highly configurable, and provides granular control over which grading categories are enabled, as well as their names and descriptions. 

Furthermore, experimental support for modifying the total grade of a submission by calculating the mean of `(automated_grade + coding_style_grades)` is also available, although it is currently not guaranteed to be bug-free.

### Minimal Configuration

If you only want to use the default configuration, you can add the following to your INGInious configuration file:

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
      merge_grades: false
```

### Parameters

#### `name`

Display name of the plugin

---

#### `enabled` (optional)

Which coding style categories to enable. Omitting this parameter enables all default categories (`comments`, `modularity`, `structure`, `idiomaticity`).

---

#### `categories` (optional)

Define new categories or redefine default categories.

##### `id`

Unique ID of category.

##### `name` (optional)

Display name of category. Defaults to `id.title()` if omitted.

##### `description`

Category description.

---

#### `experimental`

Experimental options

##### `merge_grades`

Modifies a submission's displayed grade by finding the mean of automated grading done by INGInious and Coding Style grades: 

`new_grade = (automated_grade + coding_style_grade_mean) / 2`

---

## Usage

INGInious Coding Style should be easy to use for both tutors and students. The plugin adds new buttons and displays to various existing menus in the application that can be used to add and view grades.

(All design is subject to change.)

---

### Adding Coding Style Grades (Admins & Tutors)

Find the submission to be graded.

![Find the tasks](/docs/docs/img/tutor-guide/01_tasksbutton.png)

Click on the new "Grade Coding Style" button to access the grading interface.

![Grading button](/docs/docs/img/tutor-guide/02_gradebutton.png)

Add grades and feedback (optional) to submission. 

![Grading interface](/docs/docs/img/tutor-guide/03_gradinginterface.png)

---

### Checking Grades (Students)

Students can get an overview of their coding style grades on the course's task list.

![Task list showing grades](/docs/docs/img/student-guide/01_tasklist.png)

To view detailed feedback, students can click on the new "Coding Style Grades" button in the task menu. NOTE: The button is only visible if the submission's coding style has been graded.

![Coding Style Grades task menu button](/docs/docs/img/student-guide/02_newbutton.png)

Detailed feedback is displayed similar to the admin grading interface.

![Task list showing grades](/docs/docs/img/student-guide/03_submission.png)


## Known Issues

* Not fully compatible with group submissions. Will only show the name of the first author listed for a submission.

## Developer Notes

This plugin uses [htmx](https://htmx.org/) to provide some interactivity.
