from pathlib import Path

from werkzeug.datastructures import ImmutableMultiDict

from inginious_coding_style.config import PluginConfig
from inginious_coding_style.pages.plugin_settings import (SettingsForm,
                                                          parse_settings_form)


def test_parse_settings_form(config_pydantic_full: PluginConfig):
    inp = {
        "config_path": "/some/path/to/configuration.yaml",
        "weighting": "0.25",
        "weighted_mean": "on",
        "category_description_comments": "Comments description",
        "category_description_modularity": "Modularity description",
        "bar_label_style_grade": "Style",
        "bar_enabled_style_grade": "on",
        "bar_label_total_grade": "Total",
        "bar_enabled_total_grade": "on",
        "bar_label_base_grade": "Base",
        "bar_enabled_base_grade": "on",
        "show_graders": "on",
        "submissionquery_header": "CSG",
        "submissionquery_button": "on",
        "submissionquery_priority": "3000",
    }
    form = ImmutableMultiDict(inp)
    settings_form = parse_settings_form(form, config_pydantic_full)
    assert settings_form.config_path == Path(inp["config_path"])
    assert settings_form.weighting == 0.25
    assert settings_form.weighted_mean == True
    assert settings_form.categories["comments"].description == "Comments description"
    assert (
        settings_form.categories["modularity"].description == "Modularity description"
    )
    assert settings_form.task_list_bars.total_grade.label == "Total"
    assert settings_form.task_list_bars.total_grade.enabled == True
    assert settings_form.task_list_bars.base_grade.label == "Base"
    assert settings_form.task_list_bars.base_grade.enabled == True
    assert settings_form.task_list_bars.style_grade.label == "Style"
    assert settings_form.task_list_bars.style_grade.enabled == True
    assert settings_form.submission_query.header == "CSG"
    assert settings_form.submission_query.button == True
    assert settings_form.submission_query.priority == 3000

    # Delete checkbox fields. These should now evaluate as False.
    del inp["weighted_mean"]
    del inp["bar_enabled_total_grade"]
    del inp["bar_enabled_base_grade"]
    del inp["bar_enabled_style_grade"]
    del inp["show_graders"]
    del inp["submissionquery_button"]
    form = ImmutableMultiDict(inp)

    settings_form = parse_settings_form(form, config_pydantic_full)
    assert settings_form.weighted_mean == False
    assert settings_form.task_list_bars.total_grade.enabled == False
    assert settings_form.task_list_bars.base_grade.enabled == False
    assert settings_form.task_list_bars.style_grade.enabled == False
    assert settings_form.submission_query.button == False
