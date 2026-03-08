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

    assert [node.relative_path for node in tree.markdown_files] == [
        "a.md",
        "nested/b.md",
    ]
