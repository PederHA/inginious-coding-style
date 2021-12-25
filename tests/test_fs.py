from pathlib import Path

from inginious_coding_style.fs import (chmod, chmod_rw, get_config_path,
                                       is_executable, is_readable, is_writable)


def test_get_config_path() -> None:
    p = get_config_path("tests/resources/configuration.yaml")
    assert p is not None
    assert p.exists()
    assert (
        p.absolute()
        == Path(f"{Path(__file__).parent}/resources/configuration.yaml").absolute()
    )


def test_get_config_path_not_exists() -> None:
    p = get_config_path("tests/resources/configurationz.yaml")
    assert p is None


def test_is_readable(tmp_config_file: Path) -> None:
    tmp_config_file.chmod(0o111)
    assert not is_readable(tmp_config_file)
    tmp_config_file.chmod(0o444)
    assert is_readable(tmp_config_file)


def test_is_writable(tmp_config_file: Path) -> None:
    tmp_config_file.chmod(0o111)
    assert not is_writable(tmp_config_file)
    tmp_config_file.chmod(0o222)
    assert is_writable(tmp_config_file)


def test_is_executable(tmp_config_file: Path) -> None:
    tmp_config_file.chmod(0o222)
    assert not is_executable(tmp_config_file)
    tmp_config_file.chmod(0o111)
    assert is_executable(tmp_config_file)


def test_chmod(tmp_config_file: Path) -> None:
    chmod(tmp_config_file, 0o444)
    assert not is_writable(tmp_config_file)


def test_chmod_rw(tmp_config_file: Path) -> None:
    chmod(tmp_config_file, 0o111)  # --x--x--x
    assert not is_readable(tmp_config_file)
    assert not is_writable(tmp_config_file)
    chmod_rw(tmp_config_file)  # rwx--x--x
    assert is_readable(tmp_config_file)
    assert is_writable(tmp_config_file)
