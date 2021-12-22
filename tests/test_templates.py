from inginious.frontend import plugin_manager, template_helper, user_manager

from inginious_coding_style import TEMPLATES_PATH

template_helper = template_helper.TemplateHelper(
    plugin_manager.PluginManager(),
    user_manager.UserManager(database=object(), superadmins=[]),
)


def test_render_alert_success() -> None:
    rendered = template_helper.render(
        "alert.html",
        template_folder=TEMPLATES_PATH,
        success=True,
    )
    assert rendered is not None
    assert "Success" in rendered


def test_render_alert_failure() -> None:
    rendered = template_helper.render(
        "alert.html",
        template_folder=TEMPLATES_PATH,
        success=False,
    )
    assert rendered is not None
    assert "Failure" in rendered


def test_render_alert_default() -> None:
    rendered_default = template_helper.render(
        "alert.html",
        template_folder=TEMPLATES_PATH,
    )
    rendered_failure = template_helper.render(
        "alert.html",
        template_folder=TEMPLATES_PATH,
        success=False,
    )
    assert rendered_default is not None
    assert rendered_default == rendered_failure


def test_render_alert_exception() -> None:
    rendered = template_helper.render(
        "alert.html",
        template_folder=TEMPLATES_PATH,
        exception=Exception("Something went wrong!"),
    )
    assert rendered is not None
    assert "Reason: Something went wrong!" in rendered
