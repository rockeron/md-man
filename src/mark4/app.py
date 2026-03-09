from __future__ import annotations

from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import ContentSwitcher, Footer, Header, Markdown, Static

from mark4.translator import DeepTranslatorProvider, DocumentTranslationState, Translator
from mark4.widgets import MarkdownTree


class MarkdownBrowserApp(App[None]):
    CSS_PATH = "app.tcss"
    BINDINGS = [
        ("t", "toggle_translation", "Translate"),
        ("r", "refresh_tree", "Refresh"),
        ("question_mark", "show_help", "Help"),
        ("q", "quit", "Quit"),
    ]

    TRANSLATION_WARNING = (
        "번역은 외부 번역 서비스로 문서를 전송하고 로컬 캐시에 저장할 수 있습니다. "
        "계속하려면 t를 한 번 더 누르세요."
    )

    def __init__(
        self,
        root_path: str,
        translator: Translator | None = None,
        *,
        translation_enabled: bool = True,
        persistent_cache_enabled: bool = True,
    ) -> None:
        super().__init__()
        self.root_path = Path(root_path)
        self.current_file: Path | None = None
        self.current_markdown: str | None = None
        self.current_view_markdown: str | None = None
        self.show_translation = False
        self.last_error: str | None = None
        self.translation_enabled = translation_enabled
        self.persistent_cache_enabled = persistent_cache_enabled
        self.translator = translator or DeepTranslatorProvider(
            cache_enabled=persistent_cache_enabled
        )
        self.translation_state = DocumentTranslationState()
        self._translation_request_id = 0
        self._active_translation_request_id: int | None = None
        self._scroll_positions: dict[tuple[str, str], float] = {}
        self._translation_warning_acknowledged = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            yield MarkdownTree(self.root_path)
            with ContentSwitcher(initial="viewer", id="viewer-switcher"):
                yield Static("왼쪽 트리에서 Markdown 파일을 선택하세요", id="viewer")
                yield Static("한국어 번역 준비 중...\n\n첫 번째 번역 조각을 기다리는 중입니다.", id="translation-pending")
                yield Markdown(id="markdown-view")
        yield Static(str(self.root_path), id="status")
        yield Footer()

    def on_mount(self) -> None:
        if not self.root_path.exists():
            self.last_error = "경로를 열 수 없습니다"
            self.query_one("#viewer", Static).update(self.last_error)
            self.set_status(self.last_error)
            return

        tree = self.query_one(MarkdownTree)
        tree.focus()
        if tree.first_file_node is not None:
            tree.select_node(tree.first_file_node)
            self.set_status(str(tree.first_file_node.data))
        else:
            self.set_status("이 경로 아래에 markdown 파일이 없습니다")

    def on_tree_node_selected(self, event: MarkdownTree.NodeSelected[Path]) -> None:
        path = event.node.data
        if path.is_file() and path.suffix.lower() == ".md":
            self.open_markdown(path)

    def open_markdown(self, path: Path) -> None:
        self._remember_current_scroll()
        self._cancel_translation_render_workers()
        try:
            markdown = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            self.current_view_markdown = None
            self.query_one("#viewer", Static).update("문서를 읽을 수 없습니다")
            self.query_one("#viewer-switcher", ContentSwitcher).current = "viewer"
            self.set_status(f"문서를 읽을 수 없습니다: {path}")
            return
        self.current_file = path
        self.current_markdown = markdown
        self.current_view_markdown = markdown
        self.show_translation = False
        self._active_translation_request_id = None
        viewer = self.query_one("#markdown-view", Markdown)
        viewer.update(markdown)
        self._restore_scroll_for_current_view()
        self.query_one("#viewer-switcher", ContentSwitcher).current = "markdown-view"
        self.set_status(str(path))

    def action_toggle_translation(self) -> None:
        if self.current_file is None or self.current_markdown is None:
            return

        if not self.translation_enabled:
            self.set_status("번역 기능이 비활성화되어 있습니다")
            return

        if not self._translation_warning_acknowledged:
            self._translation_warning_acknowledged = True
            self.query_one("#translation-pending", Static).update(self.TRANSLATION_WARNING)
            self.query_one("#viewer-switcher", ContentSwitcher).current = "translation-pending"
            self.set_status(self.TRANSLATION_WARNING)
            return

        path_key = str(self.current_file)
        if self.show_translation:
            self._remember_current_scroll()
            self._active_translation_request_id = None
            self._cancel_translation_render_workers()
            self.translation_state.visible_paths.discard(path_key)
            self.show_translation = False
            self.current_view_markdown = self.current_markdown
            viewer = self.query_one("#markdown-view", Markdown)
            viewer.update(self.current_markdown)
            self._restore_scroll_for_current_view()
            self.query_one("#viewer-switcher", ContentSwitcher).current = "markdown-view"
            self.set_status("번역 취소됨")
            return

        translated = self.translation_state.get_cached_translation(
            path_key,
            self.current_markdown,
        )
        if translated is None:
            translated = self.translator.get_cached_translation(
                self.current_file,
                self.current_markdown,
            )
            if translated is not None:
                self.translation_state.cache_translation(
                    path_key,
                    translated,
                    self.current_markdown,
                )

        if translated is not None:
            self._remember_current_scroll()
            self.translation_state.visible_paths.add(path_key)
            self.show_translation = True
            self.current_view_markdown = translated
            viewer = self.query_one("#markdown-view", Markdown)
            viewer.update(translated)
            self._restore_scroll_for_current_view()
            self.query_one("#viewer-switcher", ContentSwitcher).current = "markdown-view"
            self.set_status("캐시된 번역 불러옴")
            return

        self._translation_request_id += 1
        self._active_translation_request_id = self._translation_request_id
        self._remember_current_scroll()
        self.translation_state.visible_paths.add(path_key)
        self.show_translation = True
        self.current_view_markdown = ""
        self.query_one("#translation-pending", Static).update(
            "한국어 번역 준비 중...\n\n첫 번째 번역 조각을 기다리는 중입니다."
        )
        self.query_one("#viewer-switcher", ContentSwitcher).current = "translation-pending"
        self.set_status("번역 시작")
        self.run_translation_worker(
            self._translation_request_id,
            self.current_file,
            self.current_markdown,
        )

    def action_refresh_tree(self) -> None:
        if not self.root_path.exists():
            self.last_error = "경로를 열 수 없습니다"
            self.query_one("#viewer", Static).update(self.last_error)
            self.set_status(self.last_error)
            return

        tree = self.query_one(MarkdownTree)
        tree.reload_tree()
        if tree.first_file_node is not None:
            tree.select_node(tree.first_file_node)
            self.set_status("경로를 다시 스캔했습니다")
        else:
            self.query_one("#viewer", Static).update(
                "이 경로 아래에 markdown 파일이 없습니다"
            )
            self.query_one("#viewer-switcher", ContentSwitcher).current = "viewer"
            self.set_status("이 경로 아래에 markdown 파일이 없습니다")

    def action_show_help(self) -> None:
        self.set_status(
            "단축키: Enter 열기, t 번역, r 재스캔, ? 도움말, q 종료"
        )

    def set_status(self, message: str) -> None:
        self.query_one("#status", Static).update(message)

    @work(thread=True, exclusive=True, group="translation", exit_on_error=False)
    def run_translation_worker(
        self,
        request_id: int,
        path: Path,
        markdown: str,
    ) -> None:
        try:
            translated = self.translator.translate_document(
                path,
                markdown,
                on_progress=lambda partial, completed, total: self.call_from_thread(
                    self.apply_translation_progress,
                    request_id,
                    path,
                    markdown,
                    partial,
                    completed,
                    total,
                ),
            )
        except Exception as exc:
            self.call_from_thread(
                self.handle_translation_error,
                request_id,
                path,
                str(exc),
            )
            return

        self.call_from_thread(
            self.finish_translation,
            request_id,
            path,
            markdown,
            translated,
        )

    def apply_translation_progress(
        self,
        request_id: int,
        path: Path,
        markdown: str,
        partial: str,
        completed: int,
        total: int,
    ) -> None:
        if not self._should_render_translation(request_id, path):
            return

        viewer = self.query_one("#markdown-view", Markdown)
        previous = self.current_view_markdown or ""
        self.current_view_markdown = partial
        self.set_status(f"번역 중 {completed}/{total}")

        if not previous:
            self.run_worker(
                self._replace_translation_view(request_id, path, partial, True),
                group="translation-render",
                exclusive=True,
                exit_on_error=False,
            )
            return

        if partial.startswith(previous):
            delta = partial[len(previous) :]
            if not delta:
                return

            keep_bottom = viewer.max_scroll_y - viewer.scroll_y <= 1
            self.run_worker(
                self._append_translation_view(request_id, path, delta, keep_bottom),
                group="translation-render",
                exclusive=True,
                exit_on_error=False,
            )
            return

        self.run_worker(
            self._replace_translation_view(request_id, path, partial, False),
            group="translation-render",
            exclusive=True,
            exit_on_error=False,
        )

    def finish_translation(
        self,
        request_id: int,
        path: Path,
        markdown: str,
        translated: str,
    ) -> None:
        path_key = str(path)
        self.translation_state.cache_translation(path_key, translated, markdown)
        self.translation_state.visible_paths.add(path_key)

        if not self._should_render_translation(request_id, path):
            return

        self.show_translation = True
        if self.current_view_markdown != translated:
            self.current_view_markdown = translated
            self.run_worker(
                self._replace_translation_view(request_id, path, translated, False),
                group="translation-render",
                exclusive=True,
                exit_on_error=False,
            )
        else:
            self.query_one("#viewer-switcher", ContentSwitcher).current = "markdown-view"
        self.set_status("한국어 번역 보기")

    def handle_translation_error(
        self,
        request_id: int,
        path: Path,
        error_message: str,
    ) -> None:
        if not self._should_render_translation(request_id, path):
            return

        self.show_translation = False
        if self.current_markdown is not None:
            self.current_view_markdown = self.current_markdown
            viewer = self.query_one("#markdown-view", Markdown)
            viewer.update(self.current_markdown)
            self._restore_scroll_for_current_view()
        self.set_status(f"번역 실패: {error_message}")

    def _should_render_translation(self, request_id: int, path: Path) -> bool:
        return (
            self.current_file == path
            and self._active_translation_request_id == request_id
        )

    async def _replace_translation_view(
        self,
        request_id: int,
        path: Path,
        markdown: str,
        restore_saved_scroll: bool,
    ) -> None:
        if not self._should_render_translation(request_id, path):
            return

        viewer = self.query_one("#markdown-view", Markdown)
        await viewer.update(markdown)
        if not self._should_render_translation(request_id, path):
            return

        self.query_one("#viewer-switcher", ContentSwitcher).current = "markdown-view"
        if restore_saved_scroll:
            self._restore_scroll_for_current_view()

    async def _append_translation_view(
        self,
        request_id: int,
        path: Path,
        delta: str,
        keep_bottom: bool,
    ) -> None:
        if not self._should_render_translation(request_id, path):
            return

        viewer = self.query_one("#markdown-view", Markdown)
        await viewer.append(delta)
        if not self._should_render_translation(request_id, path):
            return

        self.query_one("#viewer-switcher", ContentSwitcher).current = "markdown-view"
        if keep_bottom:
            viewer.scroll_end(animate=False, immediate=False)

    def _remember_current_scroll(self) -> None:
        if self.current_file is None:
            return
        viewer = self.query_one("#markdown-view", Markdown)
        self._scroll_positions[self._scroll_key()] = viewer.scroll_y

    def _restore_scroll_for_current_view(self) -> None:
        viewer = self.query_one("#markdown-view", Markdown)
        viewer.scroll_to(
            y=self._scroll_positions.get(self._scroll_key(), 0),
            animate=False,
            immediate=True,
        )

    def _scroll_key(self) -> tuple[str, str]:
        assert self.current_file is not None
        mode = "translated" if self.show_translation else "source"
        return (str(self.current_file), mode)

    def _cancel_translation_render_workers(self) -> None:
        self.workers.cancel_group(self, "translation-render")
