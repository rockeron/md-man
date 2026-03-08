from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from deep_translator import GoogleTranslator


class Translator(Protocol):
    def translate(self, text: str) -> str: ...


class DeepTranslatorProvider:
    def __init__(self) -> None:
        self._translator = GoogleTranslator(source="auto", target="ko")

    def translate(self, text: str) -> str:
        return self._translator.translate(text)


@dataclass
class DocumentTranslationState:
    cache: dict[str, str] = field(default_factory=dict)
    visible_paths: set[str] = field(default_factory=set)

    def cache_translation(self, path: str, content: str) -> None:
        self.cache[path] = content

    def toggle(self, path: str) -> tuple[str | None, bool]:
        if path in self.visible_paths:
            self.visible_paths.remove(path)
            return None, False

        self.visible_paths.add(path)
        return self.cache.get(path), True
