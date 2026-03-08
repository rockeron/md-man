from __future__ import annotations

from pathlib import Path

from textual.widgets import Tree
from textual.widgets._tree import TreeNode


class MarkdownTree(Tree[Path]):
    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path
        self.first_file_node: TreeNode[Path] | None = None
        super().__init__(str(root_path), data=root_path, id="tree")
        self.guide_depth = 6
        self.show_root = True
        self._build_tree()

    def _build_tree(self) -> None:
        self.reset(str(self.root_path), self.root_path)
        self.root.expand()
        self.first_file_node = None

        directories: dict[Path, TreeNode[Path]] = {self.root_path: self.root}

        for path in sorted(self.root_path.rglob("*")):
            parent = directories.get(path.parent, self.root)

            if path.is_dir():
                directories[path] = parent.add(path.name, data=path, expand=True)
                continue

            if path.suffix.lower() != ".md":
                continue

            node = parent.add_leaf(path.name, data=path)
            if self.first_file_node is None:
                self.first_file_node = node
