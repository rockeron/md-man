from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import ContentSwitcher, Footer, Header, Markdown, Static

from md_man.translator import DeepTranslatorProvider, DocumentTranslationState, Translator
from md_man.widgets import MarkdownTree


class MarkdownBrowserApp(App[None]):
    CSS_PATH = "app.tcss"
    BINDINGS = [
        ("t", "toggle_translation", "Translate"),
        ("r", "refresh_tree", "Refresh"),
    ]

    def __init__(self, root_path: str, translator: Translator | None = None) -> None:
        super().__init__()
        self.root_path = Path(root_path)
        self.current_file: Path | None = None
        self.current_markdown: str | None = None
        self.current_view_markdown: str | None = None
        self.show_translation = False
        self.translator = translator or DeepTranslatorProvider()
        self.translation_state = DocumentTranslationState()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            yield MarkdownTree(self.root_path)
            with ContentSwitcher(initial="viewer", id="viewer-switcher"):
                yield Static("왼쪽 트리에서 Markdown 파일을 선택하세요", id="viewer")
                yield Markdown(id="markdown-view")
        yield Footer()

    def on_mount(self) -> None:
        tree = self.query_one(MarkdownTree)
        tree.focus()
        if tree.first_file_node is not None:
            tree.select_node(tree.first_file_node)

    def on_tree_node_selected(self, event: MarkdownTree.NodeSelected[Path]) -> None:
        path = event.node.data
        if path.is_file() and path.suffix.lower() == ".md":
            self.open_markdown(path)

    def open_markdown(self, path: Path) -> None:
        markdown = path.read_text(encoding="utf-8")
        self.current_file = path
        self.current_markdown = markdown
        self.current_view_markdown = markdown
        self.show_translation = False
        self.query_one("#markdown-view", Markdown).update(markdown)
        self.query_one("#viewer-switcher", ContentSwitcher).current = "markdown-view"

    def action_toggle_translation(self) -> None:
        if self.current_file is None or self.current_markdown is None:
            return

        path_key = str(self.current_file)
        translated = self.translation_state.cache.get(path_key)
        if translated is None:
            translated = self.translator.translate(self.current_markdown)
            self.translation_state.cache_translation(path_key, translated)

        _, is_showing_translation = self.translation_state.toggle(path_key)
        self.show_translation = is_showing_translation
        self.current_view_markdown = (
            translated if self.show_translation else self.current_markdown
        )
        self.query_one("#markdown-view", Markdown).update(self.current_view_markdown)
        self.query_one("#viewer-switcher", ContentSwitcher).current = "markdown-view"

    def action_refresh_tree(self) -> None:
        tree = self.query_one(MarkdownTree)
        tree.reload_tree()
        if tree.first_file_node is not None:
            tree.select_node(tree.first_file_node)
