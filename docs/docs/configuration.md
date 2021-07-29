# Configuration

INGInious Coding Style is highly configurable and provides granular control over which grading categories are enabled, as well as the names and descriptions of the categories.

Furthermore, experimental and cutting-edge features are made available in the `experimental` section. It is not advised to enable these settings in production. When these features are production-ready, they are moved out of the `experimental` section

## Minimal Configuration

The following YAML snipped provides the default plugin configuration, and is a good starting point to explore the plugin's functionality:

```YAML
plugins: 
-   plugin_module: inginious_coding_style
    name: "INGInious Coding Style"
```

The minimal configuration enables all default categories:
{% for category in categories.categories %} 
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
    experimental:
      merge_grades: false
```

## Parameters

### `name`

Display name of the plugin

---

### `enabled` (optional)

Which coding style categories to enable. Omitting this parameter enables all default categories (`comments`, `modularity`, `structure`, `idiomaticity`).

---

### `categories` (optional)

Define new categories or redefine default grading categories. Each category has the following parameters:

#### `id`

Unique ID of category.

#### `name` (optional)

Display name of category. Defaults to `id.title()` if omitted.

#### `description`

Description of category. This should describe the criteria used for grading.

---

### `experimental`

Experimental options

#### `merge_grades`

Modifies a submission's displayed grade by finding the mean of automated grading done by INGInious and Coding Style grades: 

`new_grade = (automated_grade + coding_style_grade_mean) / 2`

This feature is not comprehensively tested, and does not have all its features fully implemented on the frontend. As such, it is currently not advised to enable this feature.

<!-- Only display this section if we have generated data/categories.yml -->
{% if categories %}

## Default Categories

INGInious Coding Style comes with 4 default categories. If you want to change the names or descriptions of these categories, you can override them in your INGInious configuration file.

!!! attention
    The `id` parameter of a category must match if you wish to overwrite a default category. If you simply wish to disable a default category, ommit its ID from the top-level `enabled` parameter.

The default categories are defined as follows:

{% for category in categories.categories %}

### {{ category.name }}

`id`: {{ category.id }}

`name`: {{ category.name }}

`description`: {{ category.description }}

{% endfor %}

## Default Categories YAML Snippet

The following is a YAML snippet that can be added to the plugin configuration if you want to make changes to all the default categories:

```YAML
--8<-- "data/categories.yml"
```

{% endif %}
