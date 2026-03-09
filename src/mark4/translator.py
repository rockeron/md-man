from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from pathlib import Path
import shutil
from typing import Callable, Protocol

from deep_translator import GoogleTranslator
from platformdirs import user_cache_dir


ProgressCallback = Callable[[str, int, int], None]


def translation_cache_dir() -> Path:
    return Path(user_cache_dir("mark4")) / "translations"


def clear_translation_cache(cache_dir: Path | None = None) -> None:
    target = cache_dir or translation_cache_dir()
    if target.exists():
        shutil.rmtree(target)


class Translator(Protocol):
    def translate(self, text: str) -> str: ...

    def translate_document(
        self,
        path: Path | None,
        text: str,
        on_progress: ProgressCallback | None = None,
    ) -> str: ...

    def get_cached_translation(self, path: Path, text: str) -> str | None: ...


class DeepTranslatorProvider:
    def __init__(
        self,
        translator: Translator | None = None,
        max_length: int = 4000,
        cache_dir: Path | None = None,
        cache_enabled: bool = True,
    ) -> None:
        self._translator = translator or GoogleTranslator(source="auto", target="ko")
        self._max_length = max_length
        self._cache_dir = cache_dir or translation_cache_dir()
        self._cache_enabled = cache_enabled

    def translate(self, text: str) -> str:
        return self.translate_document(path=None, text=text)

    def translate_document(
        self,
        path: Path | None,
        text: str,
        on_progress: ProgressCallback | None = None,
    ) -> str:
        if path is not None:
            cached = self.get_cached_translation(path, text)
            if cached is not None:
                total_chunks = self._count_translatable_chunks(text)
                if on_progress is not None and total_chunks > 0:
                    on_progress(cached, total_chunks, total_chunks)
                return cached

        parts: list[str] = []
        completed_chunks = 0
        segments = self._build_translation_segments(text)
        total_chunks = sum(1 for is_translatable, _ in segments if is_translatable)

        for is_translatable, segment in segments:
            if not is_translatable:
                parts.append(segment)
                continue

            parts.append(self._translate_chunk(segment))
            completed_chunks += 1
            if on_progress is not None:
                on_progress("".join(parts), completed_chunks, total_chunks)

        translated = "".join(parts)
        if path is not None:
            self._write_cached_translation(path, text, translated)
        return translated

    def _translate_chunk(self, chunk: str) -> str:
        translated = self._translator.translate(chunk)
        if translated is None:
            return chunk
        return translated

    def get_cached_translation(self, path: Path, text: str) -> str | None:
        if not self._cache_enabled:
            return None
        cache_path = self._cache_path(path, text)
        if not cache_path.exists():
            return None

        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        return payload.get("translated_text")

    def _write_cached_translation(self, path: Path, text: str, translated: str) -> None:
        if not self._cache_enabled:
            return
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "path": str(path.resolve()),
            "source_hash": self._source_hash(text),
            "translated_text": translated,
        }
        self._cache_path(path, text).write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )

    def _tokenize(self, text: str) -> list[tuple[bool, str]]:
        tokens: list[tuple[bool, str]] = []
        fence_pattern = re.compile(r"(```.*?```)", re.DOTALL)
        inline_code_pattern = re.compile(r"(`[^`\n]+`)")

        for fenced_segment in fence_pattern.split(text):
            if not fenced_segment:
                continue

            if fence_pattern.fullmatch(fenced_segment):
                tokens.append((False, fenced_segment))
                continue

            for inline_segment in inline_code_pattern.split(fenced_segment):
                if not inline_segment:
                    continue

                if inline_code_pattern.fullmatch(inline_segment):
                    tokens.append((False, inline_segment))
                else:
                    tokens.append((True, inline_segment))

        return tokens

    def _build_translation_segments(self, text: str) -> list[tuple[bool, str]]:
        segments: list[tuple[bool, str]] = []
        for is_translatable, token in self._tokenize(text):
            if not is_translatable or not token.strip():
                segments.append((False, token))
                continue

            for chunk in self._split_translatable_segment(token):
                if chunk.strip():
                    segments.append((True, chunk))
                else:
                    segments.append((False, chunk))
        return segments

    def _count_translatable_chunks(self, text: str) -> int:
        return sum(1 for is_translatable, _ in self._build_translation_segments(text) if is_translatable)

    def _split_translatable_segment(self, text: str) -> list[str]:
        if len(text) <= self._max_length:
            return [text]

        blocks = re.split(r"(\n\s*\n)", text)
        return self._merge_segments(blocks)

    def _merge_segments(self, segments: list[str]) -> list[str]:
        chunks: list[str] = []
        current = ""

        for segment in segments:
            if not segment:
                continue

            if len(segment) > self._max_length:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.extend(self._split_large_segment(segment))
                continue

            if current and len(current) + len(segment) > self._max_length:
                chunks.append(current)
                current = segment
                continue

            current += segment

        if current:
            chunks.append(current)

        return chunks

    def _split_large_segment(self, segment: str) -> list[str]:
        sentence_parts = re.split(r"(?<=[.!?])(\s+)", segment)
        sentence_chunks = self._merge_segments(sentence_parts)
        if all(len(chunk) <= self._max_length for chunk in sentence_chunks):
            return sentence_chunks

        line_parts = re.split(r"(\n)", segment)
        line_chunks = self._merge_segments(line_parts)
        if all(len(chunk) <= self._max_length for chunk in line_chunks):
            return line_chunks

        return [
            segment[index : index + self._max_length]
            for index in range(0, len(segment), self._max_length)
        ]

    def _cache_path(self, path: Path, text: str) -> Path:
        cache_key = sha256(
            f"{path.resolve()}:{self._source_hash(text)}:ko:deep-translator".encode(
                "utf-8"
            )
        ).hexdigest()
        return self._cache_dir / f"{cache_key}.json"

    def _source_hash(self, text: str) -> str:
        return sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CachedTranslation:
    source_hash: str | None
    content: str


@dataclass
class DocumentTranslationState:
    cache: dict[str, CachedTranslation] = field(default_factory=dict)
    visible_paths: set[str] = field(default_factory=set)

    def cache_translation(
        self,
        path: str,
        content: str,
        source_text: str | None = None,
    ) -> None:
        source_hash = (
            sha256(source_text.encode("utf-8")).hexdigest()
            if source_text is not None
            else None
        )
        self.cache[path] = CachedTranslation(source_hash=source_hash, content=content)

    def get_cached_translation(
        self,
        path: str,
        source_text: str | None = None,
    ) -> str | None:
        cached = self.cache.get(path)
        if cached is None:
            return None

        if source_text is not None and cached.source_hash is not None:
            source_hash = sha256(source_text.encode("utf-8")).hexdigest()
            if cached.source_hash != source_hash:
                return None

        return cached.content

    def toggle(self, path: str) -> tuple[str | None, bool]:
        if path in self.visible_paths:
            self.visible_paths.remove(path)
            return None, False

        self.visible_paths.add(path)
        cached = self.cache.get(path)
        return (cached.content if cached is not None else None), True
