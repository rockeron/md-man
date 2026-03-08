# Markdown TUI Viewer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Textual application that opens a recursive markdown tree from a CLI path, renders selected markdown files, and toggles Korean translation with `t`.

**Architecture:** The app is a Python package with a small CLI entrypoint, a scanner module for recursive markdown discovery, a Textual app module for layout and key bindings, and a translator abstraction with a `deep-translator` provider. Tests cover scanning, translation state, and core app behavior before implementation code is written.

**Tech Stack:** Python 3.12+, Textual, Rich, deep-translator, pytest, pytest-asyncio

---

### Task 1: Bootstrap the Python package and CLI entrypoint

**Files:**
- Create: `pyproject.toml`
- Create: `src/md_man/__init__.py`
- Create: `src/md_man/main.py`
- Test: `tests/test_main.py`

**Step 1: Write the failing test**

```python
from md_man.main import parse_args


def test_parse_args_reads_root_path():
    args = parse_args(["/tmp/docs"])
    assert str(args.root_path) == "/tmp/docs"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py::test_parse_args_reads_root_path -v`
Expected: FAIL with `ModuleNotFoundError` or missing `parse_args`

**Step 3: Write minimal implementation**

```python
from argparse import ArgumentParser
from pathlib import Path


def parse_args(argv: list[str] | None = None):
    parser = ArgumentParser(prog="md-man")
    parser.add_argument("root_path", type=Path)
    return parser.parse_args(argv)
```

Add a `project.scripts` entry for `md-man = "md_man.main:main"` in `pyproject.toml`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py::test_parse_args_reads_root_path -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pyproject.toml src/md_man/__init__.py src/md_man/main.py tests/test_main.py
git commit -m "feat: add cli entrypoint"
```

### Task 2: Implement recursive markdown scanning

**Files:**
- Create: `src/md_man/scanner.py`
- Test: `tests/test_scanner.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from md_man.scanner import scan_markdown_tree


def test_scan_markdown_tree_returns_only_markdown_files(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# A", encoding="utf-8")
    (docs / "note.txt").write_text("ignore", encoding="utf-8")
    nested = docs / "nested"
    nested.mkdir()
    (nested / "b.md").write_text("# B", encoding="utf-8")

    tree = scan_markdown_tree(docs)

    assert [node.relative_path for node in tree.markdown_files] == ["a.md", "nested/b.md"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_scanner.py::test_scan_markdown_tree_returns_only_markdown_files -v`
Expected: FAIL with missing scanner module or function

**Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MarkdownNode:
    absolute_path: Path
    relative_path: str


@dataclass(frozen=True)
class MarkdownTree:
    root_path: Path
    markdown_files: list[MarkdownNode]


def scan_markdown_tree(root_path: Path) -> MarkdownTree:
    files = [
        MarkdownNode(path, path.relative_to(root_path).as_posix())
        for path in sorted(root_path.rglob("*.md"))
        if path.is_file()
    ]
    return MarkdownTree(root_path=root_path, markdown_files=files)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_scanner.py::test_scan_markdown_tree_returns_only_markdown_files -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/md_man/scanner.py tests/test_scanner.py
git commit -m "feat: add markdown scanner"
```

### Task 3: Add translation abstraction and toggle state

**Files:**
- Create: `src/md_man/translator.py`
- Create: `tests/test_translator.py`

**Step 1: Write the failing test**

```python
from md_man.translator import DocumentTranslationState


def test_translation_state_toggles_to_cached_korean_text():
    state = DocumentTranslationState()
    state.cache_translation("/tmp/a.md", "# 안녕하세요")

    translated, show_translation = state.toggle("/tmp/a.md")

    assert translated == "# 안녕하세요"
    assert show_translation is True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_translator.py::test_translation_state_toggles_to_cached_korean_text -v`
Expected: FAIL with missing translation state type

**Step 3: Write minimal implementation**

```python
from dataclasses import dataclass, field


@dataclass
class DocumentTranslationState:
    cache: dict[str, str] = field(default_factory=dict)
    visible_paths: set[str] = field(default_factory=set)

    def cache_translation(self, path: str, content: str) -> None:
        self.cache[path] = content

    def toggle(self, path: str) -> tuple[str | None, bool]:
        if path in self.visible_paths:
            self.visible_paths.remove(path)
            return None, False
        self.visible_paths.add(path)
        return self.cache.get(path), True
```

Add a `Translator` protocol and `DeepTranslatorProvider` wrapper around `GoogleTranslator(source="auto", target="ko")`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_translator.py::test_translation_state_toggles_to_cached_korean_text -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/md_man/translator.py tests/test_translator.py
git commit -m "feat: add translation state and provider"
```

### Task 4: Build the initial Textual shell with empty state

**Files:**
- Create: `src/md_man/app.py`
- Create: `src/md_man/app.tcss`
- Test: `tests/test_app.py`

**Step 1: Write the failing test**

```python
import pytest

from md_man.app import MarkdownBrowserApp


@pytest.mark.asyncio
async def test_app_shows_initial_guidance_when_no_file_is_selected():
    app = MarkdownBrowserApp(root_path="/tmp/docs")
    async with app.run_test() as pilot:
        assert "왼쪽 트리에서 Markdown 파일을 선택하세요" in app.query_one("#viewer").renderable.plain
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_app.py::test_app_shows_initial_guidance_when_no_file_is_selected -v`
Expected: FAIL with missing app class or viewer widget

**Step 3: Write minimal implementation**

```python
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Header, Static


class MarkdownBrowserApp(App):
    CSS_PATH = "app.tcss"

    def __init__(self, root_path: str):
        super().__init__()
        self.root_path = root_path

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield Static("tree", id="tree")
            yield Static("왼쪽 트리에서 Markdown 파일을 선택하세요", id="viewer")
        yield Footer()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_app.py::test_app_shows_initial_guidance_when_no_file_is_selected -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/md_man/app.py src/md_man/app.tcss tests/test_app.py
git commit -m "feat: add initial textual shell"
```

### Task 5: Connect the tree to markdown file loading

**Files:**
- Modify: `src/md_man/app.py`
- Create: `src/md_man/widgets.py`
- Modify: `tests/test_app.py`

**Step 1: Write the failing test**

```python
import pytest

from md_man.app import MarkdownBrowserApp


@pytest.mark.asyncio
async def test_selecting_markdown_file_renders_document(tmp_path):
    doc = tmp_path / "guide.md"
    doc.write_text("# Guide", encoding="utf-8")

    app = MarkdownBrowserApp(root_path=str(tmp_path))
    async with app.run_test() as pilot:
        await pilot.press("enter")
        assert "# Guide" in app.current_markdown
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_app.py::test_selecting_markdown_file_renders_document -v`
Expected: FAIL because selection does not load the file

**Step 3: Write minimal implementation**

```python
from pathlib import Path


def load_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class MarkdownBrowserApp(App):
    def action_open_selected(self) -> None:
        selected_path = self.tree_widget.selected_markdown_path()
        self.current_markdown = load_markdown(selected_path)
        self.viewer.update(self.current_markdown)
```

Back the tree widget with scanner results and bind `enter` to open the selected file.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_app.py::test_selecting_markdown_file_renders_document -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/md_man/app.py src/md_man/widgets.py tests/test_app.py
git commit -m "feat: render selected markdown files"
```

### Task 6: Add translation toggle and refresh behavior

**Files:**
- Modify: `src/md_man/app.py`
- Modify: `src/md_man/translator.py`
- Modify: `tests/test_app.py`

**Step 1: Write the failing test**

```python
import pytest

from md_man.app import MarkdownBrowserApp


class StubTranslator:
    def translate(self, text: str) -> str:
        return "# 번역됨"


@pytest.mark.asyncio
async def test_t_key_toggles_korean_translation(tmp_path):
    doc = tmp_path / "guide.md"
    doc.write_text("# Guide", encoding="utf-8")

    app = MarkdownBrowserApp(root_path=str(tmp_path), translator=StubTranslator())
    async with app.run_test() as pilot:
        await pilot.press("enter")
        await pilot.press("t")
        assert "# 번역됨" in app.viewer.document
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_app.py::test_t_key_toggles_korean_translation -v`
Expected: FAIL because `t` has no translation behavior

**Step 3: Write minimal implementation**

```python
class MarkdownBrowserApp(App):
    BINDINGS = [("t", "toggle_translation", "Translate")]

    async def action_toggle_translation(self) -> None:
        if not self.current_file:
            return
        translated = self.translation_state.cache.get(str(self.current_file))
        if translated is None:
            translated = self.translator.translate(self.current_markdown)
            self.translation_state.cache_translation(str(self.current_file), translated)
        self.show_translation = not self.show_translation
        self.viewer.update(translated if self.show_translation else self.current_markdown)
```

Also implement `r` to rescan the root and refresh the tree.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_app.py::test_t_key_toggles_korean_translation -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/md_man/app.py src/md_man/translator.py tests/test_app.py
git commit -m "feat: add translation toggle and refresh"
```

### Task 7: Add help, status messaging, and error states

**Files:**
- Modify: `src/md_man/app.py`
- Modify: `src/md_man/app.tcss`
- Modify: `tests/test_app.py`

**Step 1: Write the failing test**

```python
import pytest

from md_man.app import MarkdownBrowserApp


@pytest.mark.asyncio
async def test_invalid_root_path_shows_error_state():
    app = MarkdownBrowserApp(root_path="/definitely/missing")
    async with app.run_test():
        assert "경로를 열 수 없습니다" in app.screen.render_str()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_app.py::test_invalid_root_path_shows_error_state -v`
Expected: FAIL because invalid paths are not handled

**Step 3: Write minimal implementation**

```python
class MarkdownBrowserApp(App):
    def on_mount(self) -> None:
        if not Path(self.root_path).exists():
            self.status_message = "경로를 열 수 없습니다"
            self.viewer.update(self.status_message)
            return
```

Add a simple help modal or overlay for `?`, and update the footer or status line for scan and translation outcomes.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_app.py::test_invalid_root_path_shows_error_state -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/md_man/app.py src/md_man/app.tcss tests/test_app.py
git commit -m "feat: add help and error states"
```

### Task 8: Run full verification and polish package metadata

**Files:**
- Modify: `pyproject.toml`
- Review: `src/md_man/*.py`
- Review: `tests/*.py`

**Step 1: Write the failing test**

Write one final regression test if a gap appears during verification. Example:

```python
import pytest

from md_man.app import MarkdownBrowserApp


@pytest.mark.asyncio
async def test_r_key_rescans_new_markdown_files(tmp_path):
    app = MarkdownBrowserApp(root_path=str(tmp_path))
    async with app.run_test() as pilot:
        (tmp_path / "new.md").write_text("# New", encoding="utf-8")
        await pilot.press("r")
        assert "new.md" in app.tree_snapshot()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_app.py::test_r_key_rescans_new_markdown_files -v`
Expected: FAIL if refresh is incomplete

**Step 3: Write minimal implementation**

Ensure package metadata, dependency groups, and the final missing behavior are in place. Keep the implementation as small as possible.

**Step 4: Run test suite to verify it passes**

Run: `pytest -q`
Expected: all tests PASS

Run: `python -m md_man --help`
Expected: CLI usage output includes `root_path`

**Step 5: Commit**

```bash
git add pyproject.toml src/md_man tests
git commit -m "feat: finalize markdown tui viewer"
```
