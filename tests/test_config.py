from inginious_coding_style.config import get_config, DEFAULT_CATEGORIES


def test_get_config_minimal(config_raw_minimal):
    config = get_config(config_raw_minimal)
    for category in DEFAULT_CATEGORIES.values():
        assert category.id in config.enabled
        assert config.enabled[category.id] == category
    assert config_raw_minimal["name"] == config.name


def test_get_config_full(config_raw_full):
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


def test_get_config_disabled_custom_category(config_raw_full):
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
