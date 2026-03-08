import pytest
import time

from md_man.app import MarkdownBrowserApp
from textual.widgets import Markdown


class StubTranslator:
    def translate(self, text: str) -> str:
        return "# 번역됨"

    def get_cached_translation(self, path, text: str) -> str | None:
        return None

    def translate_document(self, path, text: str, on_progress=None) -> str:
        translated = self.translate(text)
        if on_progress is not None:
            on_progress(translated, 1, 1)
        return translated


class ProgressiveStubTranslator:
    def get_cached_translation(self, path, text: str) -> str | None:
        return None

    def translate(self, text: str) -> str:
        return "unused"

    def translate_document(self, path, text: str, on_progress=None) -> str:
        partials = [
            "# 1차 번역",
            "# 1차 번역\n\n본문 끝",
        ]
        total = len(partials)
        for index, partial in enumerate(partials, start=1):
            if on_progress is not None:
                on_progress(partial, index, total)
            if index != total:
                time.sleep(0.2)
        return partials[-1]


class CachedStubTranslator:
    def get_cached_translation(self, path, text: str) -> str | None:
        return "# 캐시된 번역"

    def translate(self, text: str) -> str:
        return "# 사용되면 안 됨"

    def translate_document(self, path, text: str, on_progress=None) -> str:
        raise AssertionError("cache hit should skip live translation")


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


@pytest.mark.asyncio
async def test_t_key_toggles_korean_translation(tmp_path):
    doc = tmp_path / "guide.md"
    doc.write_text("# Guide", encoding="utf-8")

    app = MarkdownBrowserApp(root_path=str(tmp_path), translator=StubTranslator())

    async with app.run_test() as pilot:
        await pilot.press("enter")
        await pilot.press("t")

        assert app.current_view_markdown == "# 번역됨"
        assert app.show_translation is True


@pytest.mark.asyncio
async def test_invalid_root_path_shows_error_state(tmp_path):
    missing = tmp_path / "missing"
    app = MarkdownBrowserApp(root_path=str(missing))

    async with app.run_test():
        viewer = app.query_one("#viewer")
        assert "경로를 열 수 없습니다" in viewer.content


@pytest.mark.asyncio
async def test_markdown_viewer_scrolls_for_long_documents(tmp_path):
    doc = tmp_path / "long.md"
    doc.write_text(
        "\n\n".join(
            f"# Title {index}\n" + ("line\n" * 20) for index in range(40)
        ),
        encoding="utf-8",
    )

    app = MarkdownBrowserApp(root_path=str(tmp_path))

    async with app.run_test() as pilot:
        await pilot.press("enter")
        viewer = app.query_one("#markdown-view", Markdown)

        assert viewer.max_scroll_y > 0


@pytest.mark.asyncio
async def test_translation_progressively_updates_the_viewer(tmp_path):
    doc = tmp_path / "guide.md"
    doc.write_text("# Guide\n\nbody", encoding="utf-8")

    app = MarkdownBrowserApp(
        root_path=str(tmp_path),
        translator=ProgressiveStubTranslator(),
    )

    async with app.run_test() as pilot:
        await pilot.press("enter")
        await pilot.press("t")
        await pilot.pause(0.05)

        assert app.current_view_markdown == "# 1차 번역"
        assert "번역 중 1/2" in app.query_one("#status").content

        await pilot.pause(0.2)

        assert app.current_view_markdown == "# 1차 번역\n\n본문 끝"
        assert app.show_translation is True


@pytest.mark.asyncio
async def test_cached_translation_is_shown_immediately(tmp_path):
    doc = tmp_path / "guide.md"
    doc.write_text("# Guide\n\nbody", encoding="utf-8")

    app = MarkdownBrowserApp(
        root_path=str(tmp_path),
        translator=CachedStubTranslator(),
    )

    async with app.run_test() as pilot:
        await pilot.press("enter")
        await pilot.press("t")

        assert app.current_view_markdown == "# 캐시된 번역"
        assert "캐시된 번역 불러옴" in app.query_one("#status").content


@pytest.mark.asyncio
async def test_pressing_t_again_restores_source_markdown(tmp_path):
    doc = tmp_path / "guide.md"
    doc.write_text("# Guide\n\nbody", encoding="utf-8")

    app = MarkdownBrowserApp(root_path=str(tmp_path), translator=StubTranslator())

    async with app.run_test() as pilot:
        await pilot.press("enter")
        await pilot.press("t")
        await pilot.press("t")

        assert app.current_view_markdown == "# Guide\n\nbody"
        assert "번역 취소됨" in app.query_one("#status").content
