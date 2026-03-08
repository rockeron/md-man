from pathlib import Path
import tomllib


def _load_pyproject() -> dict:
    return tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))


def test_pyproject_has_public_package_metadata():
    pyproject = _load_pyproject()
    project = pyproject["project"]

    assert project["readme"] == "README.md"
    assert project["license"] == "MIT"
    assert project["license-files"] == ["LICENSE"]
    assert project["authors"]
    assert project["urls"]["Homepage"] == "https://github.com/rockeron/md-man"
    assert project["urls"]["Repository"] == "https://github.com/rockeron/md-man"
    assert "Topic :: Text Processing :: Markup :: Markdown" in project["classifiers"]
    assert "License :: OSI Approved :: MIT License" not in project["classifiers"]


def test_pyproject_includes_textual_css_as_package_data():
    pyproject = _load_pyproject()

    assert pyproject["tool"]["setuptools"]["package-data"]["md_man"] == ["app.tcss"]
