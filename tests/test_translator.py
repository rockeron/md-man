from pathlib import Path

from mark4.translator import (
    DeepTranslatorProvider,
    DocumentTranslationState,
    clear_translation_cache,
)


def test_translation_state_toggles_to_cached_korean_text():
    state = DocumentTranslationState()
    state.cache_translation("/tmp/a.md", "# 안녕하세요")

    translated, show_translation = state.toggle("/tmp/a.md")

    assert translated == "# 안녕하세요"
    assert show_translation is True


class RecordingTranslator:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def translate(self, text: str) -> str:
        self.calls.append(text)
        return text.upper()


class NoneReturningTranslator:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def translate(self, text: str) -> str | None:
        self.calls.append(text)
        if len(self.calls) == 1:
            return None
        return text.upper()


class FailingTranslator:
    def translate(self, text: str) -> str:
        raise AssertionError("persistent cache should have been used")


def test_deep_translator_provider_splits_long_text_into_chunks():
    translator = RecordingTranslator()
    provider = DeepTranslatorProvider(translator=translator, max_length=40)
    source = ("first paragraph\n\nsecond paragraph\n\n" * 4).strip()

    translated = provider.translate(source)

    assert translated == source.upper()
    assert len(translator.calls) > 1
    assert all(len(call) <= 40 for call in translator.calls)


def test_deep_translator_provider_preserves_code_blocks_and_inline_code():
    translator = RecordingTranslator()
    provider = DeepTranslatorProvider(translator=translator, max_length=200)
    source = (
        "hello `code_sample()` world\n\n"
        "```python\n"
        "print('keep me')\n"
        "```\n\n"
        "bye"
    )

    translated = provider.translate(source)

    assert translated == (
        "HELLO `code_sample()` WORLD\n\n"
        "```python\n"
        "print('keep me')\n"
        "```\n\n"
        "BYE"
    )


def test_deep_translator_provider_falls_back_to_original_chunk_on_none_response():
    translator = NoneReturningTranslator()
    provider = DeepTranslatorProvider(translator=translator, max_length=20)
    source = "first paragraph\n\nsecond paragraph"

    translated = provider.translate(source)

    assert translated == "first paragraph\n\nSECOND PARAGRAPH"


def test_deep_translator_provider_reuses_persistent_cache_across_instances(tmp_path):
    source_path = Path("/tmp/example.md")
    source = "hello world"
    first = DeepTranslatorProvider(
        translator=RecordingTranslator(),
        cache_dir=tmp_path,
        max_length=100,
    )

    translated = first.translate_document(source_path, source)

    second = DeepTranslatorProvider(
        translator=FailingTranslator(),
        cache_dir=tmp_path,
        max_length=100,
    )

    cached = second.translate_document(source_path, source)

    assert translated == "HELLO WORLD"
    assert cached == translated


def test_deep_translator_provider_can_disable_persistent_cache(tmp_path):
    source_path = Path("/tmp/example.md")
    source = "hello world"
    provider = DeepTranslatorProvider(
        translator=RecordingTranslator(),
        cache_dir=tmp_path,
        cache_enabled=False,
    )

    translated = provider.translate_document(source_path, source)

    assert translated == "HELLO WORLD"
    assert provider.get_cached_translation(source_path, source) is None
    assert list(tmp_path.iterdir()) == []


def test_clear_translation_cache_removes_cache_directory(tmp_path):
    cache_file = tmp_path / "translations" / "cached.json"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_text("{}", encoding="utf-8")

    clear_translation_cache(cache_file.parent)

    assert not cache_file.parent.exists()
