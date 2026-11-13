# tests/test_chunking.py
"""
Tests for the chunking rules. These are pure functions: no database and no network.
Run from backend/: python -m pytest -q tests/test_chunking.py
"""

import re

import pytest

from app.services import chunking_service
from app.services.chunking_service import chunk_text, page_number_at

SENTENCE_END = re.compile(r"[^.!?]*[.!?]+")


def _sentences(text: str) -> list[str]:
    return [match.group(0).strip() for match in SENTENCE_END.finditer(text)]


def _numbered_sentences(count: int, prefix: str = "The system records step") -> str:
    return " ".join(f"{prefix} {number} of the review process." for number in range(1, count + 1))


def test_short_text_is_one_chunk_equal_to_the_original():
    text = "Hello discovery. This is short."

    chunks = chunk_text(text)

    assert len(chunks) == 1
    assert chunks[0].chunk_number == 1
    assert chunks[0].text == text
    assert (chunks[0].start_char, chunks[0].end_char) == (0, len(text))


def test_long_text_is_split_and_each_chunk_fits_the_limit():
    text = _numbered_sentences(40)

    chunks = chunk_text(text, max_chars=300, overlap_chars=80)

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 300 for chunk in chunks)


def test_every_chunk_is_an_exact_slice_of_the_source_text():
    text = "2. Data Flow\n\n" + _numbered_sentences(30) + "\n\nA closing paragraph follows here."

    chunks = chunk_text(text, max_chars=300, overlap_chars=80)

    assert [chunk.chunk_number for chunk in chunks] == list(range(1, len(chunks) + 1))
    for chunk in chunks:
        assert text[chunk.start_char : chunk.end_char] == chunk.text


def test_consecutive_chunks_share_whole_sentences_within_the_overlap_limit():
    text = _numbered_sentences(40)
    overlap_chars = 120

    chunks = chunk_text(text, max_chars=300, overlap_chars=overlap_chars)

    for previous, following in zip(chunks, chunks[1:]):
        shared = previous.end_char - following.start_char
        assert 0 < shared <= overlap_chars
        shared_text = text[following.start_char : previous.end_char]
        assert shared_text.rstrip()[-1] in ".!?"  # the overlap ends on a whole sentence


def test_every_sentence_appears_in_at_least_one_chunk():
    text = _numbered_sentences(40)

    chunks = chunk_text(text, max_chars=300, overlap_chars=120)

    for sentence in _sentences(text):
        assert any(sentence in chunk.text for chunk in chunks), sentence


def test_heading_is_never_the_last_text_in_a_chunk():
    headings = ["1. Scope", "2. Data Flow", "3. Storage Rules"]
    blocks = []
    for heading in headings:
        blocks.append(heading)
        blocks.append(_numbered_sentences(6, prefix=heading.split(". ")[1]))
    text = "\n\n".join(blocks)

    chunks = chunk_text(text, max_chars=260, overlap_chars=60)

    for heading in headings:
        for chunk in chunks:
            assert not chunk.text.rstrip().endswith(heading)
        holder = next(chunk for chunk in chunks if heading in chunk.text)
        assert holder.text.index(heading) < len(holder.text) - len(heading)


def test_paragraph_that_fits_in_one_chunk_is_not_split():
    paragraphs = [_numbered_sentences(4, prefix=f"Paragraph {letter} sentence") for letter in "ABC"]
    text = "\n\n".join(paragraphs)

    chunks = chunk_text(text, max_chars=400, overlap_chars=0)

    for paragraph in paragraphs:
        assert any(paragraph in chunk.text for chunk in chunks)


def test_sentence_longer_than_the_limit_is_cut_at_a_word_boundary():
    long_sentence = " ".join(["alpha"] * 200) + "."
    text = "Intro sentence here. " + long_sentence

    chunks = chunk_text(text, max_chars=120, overlap_chars=30)

    assert len(chunks) > 2
    for chunk in chunks:
        assert len(chunk.text) <= 120
        assert chunk.start_char == 0 or text[chunk.start_char - 1].isspace()
        assert chunk.end_char == len(text) or text[chunk.end_char].isspace()


def test_a_single_word_longer_than_the_limit_is_cut_at_the_limit():
    text = "x" * 250

    chunks = chunk_text(text, max_chars=100, overlap_chars=10)

    assert all(len(chunk.text) <= 100 for chunk in chunks)
    assert "".join(chunk.text for chunk in chunks[:1]) == "x" * 100


def test_tail_merge_joins_a_tiny_chunk_when_the_result_fits():
    spans = [(0, 400), (380, 470)]  # tail is 90 chars, merged span is 470

    merged = chunking_service._merge_tiny_tail(spans, max_chars=500)

    assert merged == [(0, 470)]


def test_tail_merge_keeps_the_tail_when_the_merge_would_be_too_large():
    spans = [(0, 400), (380, 470)]

    assert chunking_service._merge_tiny_tail(spans, max_chars=450) == spans


def test_tail_merge_keeps_a_tail_of_200_characters_or_more():
    spans = [(0, 100), (50, 260)]  # tail is 210 chars

    assert chunking_service._merge_tiny_tail(spans, max_chars=1000) == spans


@pytest.mark.parametrize("text", ["", "   ", "\n\n\t  \n"])
def test_empty_or_whitespace_only_text_returns_no_chunks(text):
    assert chunk_text(text) == []


@pytest.mark.parametrize("overlap", [1000, 1001])
def test_overlap_not_smaller_than_max_raises_value_error(overlap):
    with pytest.raises(ValueError):
        chunk_text("Some text. More text.", max_chars=1000, overlap_chars=overlap)


def test_stored_text_is_never_trimmed_or_normalised():
    text = "  Leading spaces.   Double  spaces stay.\n\n\nTabs\there.  "

    chunks = chunk_text(text, max_chars=1000, overlap_chars=100)

    assert chunks[0].text == "Leading spaces.   Double  spaces stay.\n\n\nTabs\there."
    assert text[chunks[0].start_char : chunks[0].end_char] == chunks[0].text


def test_page_number_comes_from_the_last_page_marker_before_the_offset():
    text = "Page 1:\nFirst page text.\nPage 2:\nSecond page text."
    second_page_start = text.index("Second")

    assert page_number_at(text, 0) == 1
    assert page_number_at(text, second_page_start) == 2


def test_page_number_is_none_without_markers():
    assert page_number_at("Plain text with no pages.", 5) is None
