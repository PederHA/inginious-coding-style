# INGInious Coding Style Grader

A plugin for INGInious that aims to allow teachers to grade several aspect of a student submission's code style.

## Installation

```bash
pip install inginious-coding-style
```

## Configuration

Add the following section to your `configuration.yaml` under the `plugin` key:

```yml
-   plugin_module: inginious_coding_style
    name: "INGInious Coding Style"
    enabled:
        - comments
        - modularity
        - structure
        - idiomaticity
```

### Parameters

#### `name`

Display name of the plugin

#### `enabled`

Which coding style categories to enable. Omitting this parameter enables all categories.


## Usage

WIP
