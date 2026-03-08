from md_man.translator import DocumentTranslationState


def test_translation_state_toggles_to_cached_korean_text():
    state = DocumentTranslationState()
    state.cache_translation("/tmp/a.md", "# 안녕하세요")

    translated, show_translation = state.toggle("/tmp/a.md")

    assert translated == "# 안녕하세요"
    assert show_translation is True
