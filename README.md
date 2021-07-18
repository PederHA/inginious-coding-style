# INGInious Coding Style Grader

A plugin for INGInious that aims to allow teachers to grade several aspect of a student submission's code style.

## Installation

```bash
pip install inginious-coding-style
```

## Configuration

The plugin exposes the following configuration which should be added to your INGInious configuration file.

```yml
plugins: 
-   plugin_module: inginious_coding_style
    name: "INGInious Coding Style"
    enabled:
        # enables all default categories + 1 custom
        - comments
        - modularity
        - structure
        - idiomaticity
        - coolness
    categories: # optional
        # This is a definition for a new category
      - id: coolness
        name: Coolness
        description: How cool the code looks B-)
      # This redefines a default category
      - id: comments
        name: Kommentering
        description: Hvor godt kommentert koden er.
```

### Parameters

#### `name`

Display name of the plugin

#### `enabled` (optional)

Which coding style categories to enable. Omitting this parameter enables all default categories (`comments`, `modularity`, `structure`, `idiomaticity`).

#### `categories` (optional)

Define new categories or redefine default categories.

##### `id`

Unique ID of category.

##### `name` (optional)

Display name of category. Defaults to `id.title()` if omitted.

##### `description`

Category description.


## Usage

WIP
