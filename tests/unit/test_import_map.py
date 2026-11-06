from scripts.map_project_imports import map_imports


def test_cycles_are_detected_without_execution(tmp_path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "__init__.py").write_text("")
    (source / "a.py").write_text("from src import b\nraise RuntimeError('do not run')\n")
    (source / "b.py").write_text("from . import a\n")
    result = map_imports(tmp_path)
    assert result["cycles"] == [["src.a", "src.b"]]
    assert "src.b" in result["dependencies"]["src.a"]


def test_relative_imports_resolve_in_nested_packages(tmp_path) -> None:
    package = tmp_path / "src" / "nested"
    package.mkdir(parents=True)
    (tmp_path / "src/__init__.py").write_text("")
    (package / "__init__.py").write_text("")
    (package / "a.py").write_text("from . import b\n")
    (package / "b.py").write_text("")
    result = map_imports(tmp_path)
    assert result["cycles"] == []
    assert "src.nested.b" in result["dependencies"]["src.nested.a"]
