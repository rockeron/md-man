from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import ContentSwitcher, Footer, Header, Markdown, Static

from md_man.widgets import MarkdownTree


class MarkdownBrowserApp(App[None]):
    CSS_PATH = "app.tcss"

    def __init__(self, root_path: str) -> None:
        super().__init__()
        self.root_path = Path(root_path)
        self.current_file: Path | None = None
        self.current_markdown: str | None = None

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
        self.query_one("#markdown-view", Markdown).update(markdown)
        self.query_one("#viewer-switcher", ContentSwitcher).current = "markdown-view"
