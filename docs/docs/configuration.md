# Configuration

INGInious Coding Style is highly configurable, and provides granular control over which grading categories are enabled, as well as their names and descriptions.

Furthermore, experimental support for modifying the total grade of a submission by calculating the mean of `(automated_grade + coding_style_grades)` is also available, although it is currently not guaranteed to be bug-free.

## Minimal Configuration

If you only want to use the default configuration, you can add the following to your INGInious configuration file:

```YAML
plugins: 
-   plugin_module: inginious_coding_style
    name: "INGInious Coding Style"
```

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

Define new categories or redefine default categories.

#### `id`

Unique ID of category.

#### `name` (optional)

Display name of category. Defaults to `id.title()` if omitted.

#### `description`

Category description.

---

### `experimental`

Experimental options

#### `merge_grades`

Modifies a submission's displayed grade by finding the mean of automated grading done by INGInious and Coding Style grades: 

`new_grade = (automated_grade + coding_style_grade_mean) / 2`