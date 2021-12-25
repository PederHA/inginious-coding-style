from typing import TYPE_CHECKING

from inginious.common import custom_yaml

from inginious_coding_style.config import DEFAULT_CATEGORIES, get_config

if TYPE_CHECKING:
    from typing import Any, OrderedDict


def test_get_config_minimal(config_raw_minimal: dict):
    config = get_config(config_raw_minimal)
    for category in DEFAULT_CATEGORIES.values():
        assert category.id in config.enabled
        assert config.enabled[category.id] == category
    assert config_raw_minimal["name"] == config.name


def test_get_config_full(config_raw_full: dict):
    config = get_config(config_raw_full)
    for category in DEFAULT_CATEGORIES.values():
        assert category.id in config.enabled
        assert config.enabled[category.id] == category
    assert (
        config.enabled["custom_category"].id == config_raw_full["categories"][0]["id"]
    )
    assert (
        config.enabled["custom_category"].name
        == config_raw_full["categories"][0]["name"]
    )
    assert (
        config.enabled["custom_category"].description
        == config_raw_full["categories"][0]["description"]
    )


def test_get_config_disabled_custom_category(config_raw_full: dict):
    """Tests that a custom category is not enabled if it is not included in `config["enabled"]`."""
    # NOTE: This just tests expected behavior, but whether or not this SHOULD
    # be the expected behavior is a very valid question.
    #
    # Should custom categories be enabled by default, or should they adhere to
    # the same rules as built-in categories (i.e. needing to be enabled by
    # adding them to "enabled")? As of now, they MUST be enabled manually.
    config_raw_full["enabled"].remove("custom_category")
    config = get_config(config_raw_full)
    assert "custom_category" not in config.enabled


def test_inginious_config_parser():
    """This test ensured continued compatibility with future INGInious versions
    by testing INGInious's YAML parser.
    """
    with open("tests/resources/configuration.yaml", "r", encoding="utf-8") as f:
        conf = custom_yaml.load(f)  # type: OrderedDict[str, Any]
    # Get the plugin config. Fails if it can't be found
    plugin_config = next(
        x for x in conf["plugins"] if x["plugin_module"] == "inginious_coding_style"
    )  # type: OrderedDict[str, Any]

    assert plugin_config["name"] == "INGInious Coding Style"

    # Enabled
    assert all(
        e in ["comments", "modularity", "structure", "idiomaticity", "custom_category"]
        for e in plugin_config["enabled"]
    )

    # Categories
    assert len(plugin_config["categories"]) == 2
    assert plugin_config["categories"][0]["id"] == "custom_category"
    assert plugin_config["categories"][0]["name"] == "Custom Category"
    assert plugin_config["categories"][0]["description"] == "This is a custom category."
    assert plugin_config["categories"][1]["id"] == "comments"
    assert plugin_config["categories"][1]["name"] == "Kommentering"
    assert (
        plugin_config["categories"][1]["description"]
        == "Hvor godt kommentert koden er."
    )

    # Submission Query
    assert plugin_config["submission_query"]["header"] == "CSG"
    assert plugin_config["submission_query"]["priority"] == 3000
    assert plugin_config["submission_query"]["button"] == True

    # Weighted Mean
    assert plugin_config["weighted_mean"]["enabled"] == True
    assert plugin_config["weighted_mean"]["weighting"] == 0.25
