# Configuration

INGInious Coding Style is highly configurable and provides granular control of the majority of its features. Despite this, extensive configuration is not necessary, as the plugin tries to implement sensible defaults, and therefore should just work straight out of the box.

## Minimal Configuration

The following YAML snippet provides the default plugin configuration, and is a good starting point for exploring the plugin's functionality:

```YAML
plugins:
-   plugin_module: inginious_coding_style
    name: "INGInious Coding Style"
```

The minimal configuration enables all default categories:
{% for category in categories %}
[`{{ category.id }}`](#{{ category.id }}){% endfor %}.

See [Default Categories](#default-categories) for more information about the default categories.

## Full Configuration

Below is an example of a configuration making use of all available configuration options.

```YAML
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
        priority: 3000
        button: true
    weighted_mean:
        enabled: true
        weighting: 0.25
        round: true
        round_digits: 2
    task_list_bars:
        total_grade:
            enabled: true
            label: Grade
        base_grade:
            enabled: true
            label: Completion
        style_grade:
            enabled: true
            label: Coding Style
    show_graders: false
```
<!-- TODO: https://squidfunk.github.io/mkdocs-material/reference/data-tables/#configuration -->
{% macro get_schema(prop, id="", required=none) -%}
<!-- ##### Schema: -->

```YAML
{% for k, v in prop.items() -%}
  {% if k != "title" -%}
   {#- HACK: Add quotes to strings in default value -#}
    {{ k }}: {% if k == "default" and v is string -%}
      '{{ v }}'
    {%- else -%}
      {{ v }}
    {%- endif -%}
  {%- endif %}
{% endfor -%}
required: {% if required is not none -%} {{ id in required }} {% else -%} {{ False }} {%- endif %}
```
{% endmacro %}

## Parameters

### `name`

Display name of the plugin

{{ get_schema(schema.properties.name, "name") }}

---

### `enabled`

Which coding style categories to enable. Omitting this parameter enables all default categories (
  {%- for category in categories -%}
    `{{ category.id }}`
  {% endfor -%}).

{{ get_schema(schema.properties.enabled, "enabled") }}

---

### `categories`

Define new grading categories or modify default grading categories.

Each category has the following parameters:

{% set required = schema.definitions.GradingCategory.required %}
#### `id`

Unique ID of the category.


{{ get_schema(schema.definitions.GradingCategory.properties.id, "id", required) }}

#### `name`

Display name of category. Defaults to `id.title()` if omitted.

{{ get_schema(schema.definitions.GradingCategory.properties.id, "name", required) }}

#### `description`

Description of category. This should describe the criteria used for grading.

{{ get_schema(schema.definitions.GradingCategory.properties.id, "description", required) }}

---

### `submission_query`

Settings for the submissions query results table (`/admin/<courseid>/submissions`).

#### `header`

The header text for the plugin's column in the query results table.

{{ get_schema(schema.definitions.SubmissionQuerySettings.properties.header) }}

#### `button`

Adds an additional button to each search result row that links to the submission's coding style grading page.

{{ get_schema(schema.definitions.SubmissionQuerySettings.properties.button) }}

#### `priority`

The priority of the plugin hook. The priority must be a number that is unique to the plugin in order to avoid column ordering issues. In cases where the plugin's header does not match its corresponding column in the table body, try to change `priority` to a different number. Given the low number of INGInious plugins in existence, this should virtually never happen, though.

{{ get_schema(schema.definitions.SubmissionQuerySettings.properties.priority) }}

---

### `weighted_mean`

Calculates a new grade for submissions after they have received coding style grades by finding the mean of automated INGInious grade and coding style grades:

`new_grade = (automated_grade * (1 - weighting)) + (coding_style_grade_mean * weighting)`

**Example**

```pycon
>>> automated_grade = 100
>>> mean_style_grade = 80
>>> weighting = 0.25
>>> new_grade = (automated_grade * (1-weighting)) + (mean_style_grade * weighting)
>>> new_grade
95.0
```

#### `enabled`

Enable weighted mean grade calculation.

{{ get_schema(schema.definitions.WeightedMeanSettings.properties.enabled) }}


#### `weighting`

How much of the final grade the coding style grades should make up.

##### Example

```py
weighting = 0.25
base_grade_weight = 1 - weighting
base_grade_weight == 0.75
```

When `weighting` is set to 0.25, the style grades will make up 25% of the submission's final grade, while its base grade will make up the remaining 75%.

{{ get_schema(schema.definitions.WeightedMeanSettings.properties.weighting) }}

#### `round`

Whether to round the weighted mean grade or not.

{{ get_schema(schema.definitions.WeightedMeanSettings.properties.round) }}

#### `round_digits`

Number of digits after decimal point to round to. Has no effect if `round` is disabled.

{{ get_schema(schema.definitions.WeightedMeanSettings.properties.round_digits) }}

### `task_list_bars`

Settings for the various bars displayed on the task list.

#### `total_grade`

The bar displaying the submission's final grade. This bar cannot be disabled, but its label can be.

##### `enabled`

Visibility of the total grade bar's label.

{{ get_schema(schema.definitions.TotalGradeBar.properties.enabled) }}

##### `label`

Label for the total grade bar.

{{ get_schema(schema.definitions.TotalGradeBar.properties.enabled) }}

---

#### `base_grade`

The bar displaying the submission's base grade (the grade given by the automatic INGInious grader). This bar can be disabled in its entirety.

##### `enabled`

Visibility of the base grade bar. Has no effect if `weighted_mean` is disabled.

{{ get_schema(schema.definitions.BaseGradeBar.properties.enabled) }}

##### `label`

Label for the total grade bar.

{{ get_schema(schema.definitions.BaseGradeBar.properties.enabled) }}

---

#### `style_grade`

The bar displaying the submission's mean coding style grade. This bar can be disabled in its entirety.

##### `enabled`

Visibility of the coding style grade bar.

{{ get_schema(schema.definitions.StyleGradeBar.properties.enabled) }}

##### `label`

Label for the coding style grade bar.

{{ get_schema(schema.definitions.StyleGradeBar.properties.enabled) }}

---

![task_list_bar preview](img/configuration/01_task_list_bar.png)

---

### `show_graders`

Display a list of tutors/admins who have graded the submission in the sidebar of a student submissions coding style grade page (`/submissions/<submissionid>/codingstyle`).

{{ get_schema(schema.properties.show_graders) }}

<!-- Only display this section if we have generated data/categories.-->
{% if categories %}

## Default Categories

INGInious Coding Style comes with {{ categories | length }} default grading categories. If you want to change the names or descriptions of these categories, you can override them in your INGInious configuration file.

!!! attention
    The `id` parameter of a category must match the default category's ID if you wish to overwrite a default category. If you simply wish to disable a default category, omit its ID from the top-level `enabled` parameter.

The following is a YAML snippet that includes the definitions for all default categories, which can be added to the plugin configuration should you wish to expand on the existing decriptions or otherwise modify the categories:

```YAML
--8<-- "data/categories.yml"
```

{% endif %}
