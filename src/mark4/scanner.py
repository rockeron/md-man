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
    markdown_files: list[MarkdownNode] = []

    def on_error(error: OSError) -> None:
        return None

    for current_root, _, filenames in root_path.walk(on_error=on_error):
        for filename in sorted(filenames):
            if not filename.lower().endswith(".md"):
                continue

            path = current_root / filename
            markdown_files.append(
                MarkdownNode(
                    absolute_path=path,
                    relative_path=path.relative_to(root_path).as_posix(),
                )
            )

    markdown_files.sort(key=lambda node: node.relative_path)
    return MarkdownTree(root_path=root_path, markdown_files=markdown_files)
