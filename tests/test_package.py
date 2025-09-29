from wv import get_version


def test_get_version_returns_string() -> None:
    version = get_version()
    assert isinstance(version, str)
