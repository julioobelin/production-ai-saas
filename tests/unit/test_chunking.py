import pytest

from app.ai.chunking import chunk_text


def test_short_paragraphs_stay_intact() -> None:
    chunks = chunk_text("Alpha paragraph.\n\nBeta paragraph.", size=80, overlap=10)
    assert chunks == ["Alpha paragraph.", "Beta paragraph."]


def test_single_newlines_do_not_split_a_paragraph() -> None:
    chunks = chunk_text("line one\nline two", size=80, overlap=10)
    assert chunks == ["line one\nline two"]


def test_long_paragraph_uses_window_and_overlap() -> None:
    chunks = chunk_text("abcdefghijk", size=10, overlap=2)
    assert chunks == ["abcdefghij", "ijk"]


def test_blank_text_has_no_chunks() -> None:
    assert chunk_text("  \n\n  ", size=80, overlap=10) == []


def test_overlap_must_be_smaller_than_size() -> None:
    with pytest.raises(ValueError):
        chunk_text("abcdef", size=4, overlap=4)
