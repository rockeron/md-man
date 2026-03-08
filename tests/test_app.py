import pytest

from md_man.app import MarkdownBrowserApp


@pytest.mark.asyncio
async def test_app_shows_initial_guidance_when_no_file_is_selected(tmp_path):
    app = MarkdownBrowserApp(root_path=str(tmp_path))

    async with app.run_test():
        viewer = app.query_one("#viewer")
        assert "왼쪽 트리에서 Markdown 파일을 선택하세요" in viewer.content


@pytest.mark.asyncio
async def test_selecting_markdown_file_renders_document(tmp_path):
    doc = tmp_path / "guide.md"
    doc.write_text("# Guide", encoding="utf-8")

    app = MarkdownBrowserApp(root_path=str(tmp_path))

    async with app.run_test() as pilot:
        await pilot.press("enter")
        assert app.current_markdown == "# Guide"
