"""Private Docker setup never overwrites saved configuration or credentials."""

import pytest

from scripts.prepare_local_docker import prepare


def test_preparation_is_non_destructive(tmp_path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    assert len(prepare(tmp_path, cache)) == 2
    password = (tmp_path / ".local/postgres_password").read_bytes()
    settings = (tmp_path / ".env.docker").read_bytes()
    assert len(password) >= 32
    assert password not in settings
    assert prepare(tmp_path, cache) == []
    assert (tmp_path / ".local/postgres_password").read_bytes() == password
    assert (tmp_path / ".env.docker").read_bytes() == settings


def test_missing_cache_does_not_create_secret(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        prepare(tmp_path, tmp_path / "missing")
    assert not (tmp_path / ".local").exists()
