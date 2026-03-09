from pathlib import Path

from mark4.main import parse_args


def test_parse_args_reads_root_path():
    args = parse_args(["/tmp/docs"])
    assert str(args.root_path) == "/tmp/docs"


def test_parse_args_reads_public_safety_flags():
    args = parse_args(["--no-translate", "--no-cache", "/tmp/docs"])

    assert args.no_translate is True
    assert args.no_cache is True
    assert args.clear_cache is False


def test_main_clears_translation_cache_without_running_app(tmp_path, monkeypatch):
    cleared: list[Path] = []

    def fake_clear_cache(cache_dir: Path | None = None) -> None:
        cleared.append(cache_dir or Path("default"))

    monkeypatch.setattr("mark4.main.clear_translation_cache", fake_clear_cache)

    class StubApp:
        def __init__(self, root_path: str, **kwargs) -> None:
            raise AssertionError("app should not be created when clearing cache")

    from mark4.main import main

    exit_code = main(["--clear-cache", str(tmp_path)], app_factory=StubApp)

    assert exit_code == 0
    assert cleared


def test_main_runs_app_with_root_path(tmp_path):
    calls: list[object] = []

    class StubApp:
        def __init__(
            self,
            root_path: str,
            *,
            translation_enabled: bool,
            persistent_cache_enabled: bool,
        ) -> None:
            calls.append(root_path)
            calls.append(translation_enabled)
            calls.append(persistent_cache_enabled)

        def run(self) -> None:
            calls.append("run")

    from mark4.main import main

    exit_code = main([str(tmp_path)], app_factory=StubApp)

    assert exit_code == 0
    assert calls == [str(tmp_path), True, True, "run"]
