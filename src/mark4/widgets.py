from __future__ import annotations

from pathlib import Path

from mark4.scanner import scan_markdown_tree
from textual.widgets import Tree
from textual.widgets._tree import TreeNode


class MarkdownTree(Tree[Path]):
    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path
        self.first_file_node: TreeNode[Path] | None = None
        super().__init__(str(root_path), data=root_path, id="tree")
        self.guide_depth = 6
        self.show_root = True
        self.reload_tree()

    def reload_tree(self) -> None:
        self.reset(str(self.root_path), self.root_path)
        self.root.expand()
        self.first_file_node = None

        directories: dict[Path, TreeNode[Path]] = {self.root_path: self.root}

        for markdown_file in scan_markdown_tree(self.root_path).markdown_files:
            path = markdown_file.absolute_path
            current_parent = self.root_path
            parent_node = self.root

            for part in path.relative_to(self.root_path).parts[:-1]:
                current_parent = current_parent / part
                if current_parent not in directories:
                    directories[current_parent] = parent_node.add(
                        part,
                        data=current_parent,
                        expand=True,
                    )
                parent_node = directories[current_parent]

            node = parent_node.add_leaf(path.name, data=path)
            if self.first_file_node is None:
                self.first_file_node = node
