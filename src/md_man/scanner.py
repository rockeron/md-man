from __future__ import annotations

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
    markdown_files = [
        MarkdownNode(
            absolute_path=path,
            relative_path=path.relative_to(root_path).as_posix(),
        )
        for path in sorted(root_path.rglob("*.md"))
        if path.is_file()
    ]
    return MarkdownTree(root_path=root_path, markdown_files=markdown_files)
