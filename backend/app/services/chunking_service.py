"""
Splits extracted text into overlapping chunks that can be traced back to exact characters.

Analogy: cutting a long printed report into numbered strips for a filing cabinet.
Each strip is cut along sentence lines, never through a word, and carries the
position of its first and last character in the original report (start_char,
end_char). Neighbouring strips share a sentence or two, so an idea that falls on
a cut still appears whole on one strip.

Correctness: this module never edits the text. Every chunk is a slice of the
original string, so content_text[start_char:end_char] == chunk.text is always true.
Nothing here touches the database, which keeps the rules easy to test on their own.
"""

import re
from dataclasses import dataclass

# A chunk shorter than this at the very end is merged into the chunk before it.
TINY_TAIL_CHARS = 200

# A single line up to this long, with no full stop, is treated as a heading.
HEADING_MAX_CHARS = 100

# One or more blank lines separate paragraphs. \r is allowed for Windows line endings.
_BLANK_LINE = re.compile(r"\n[ \t\r\f\v]*\n")

# A sentence ends at . ! or ? (one or more) followed by whitespace or the end of the text.
_SENTENCE_END = re.compile(r"[.!?]+(?=\s|$)")

# The number at the start of a line in a list, such as "2" in "2. Data Flow".
# A full stop after it is part of the numbering, not the end of a sentence.
_LIST_NUMBER = re.compile(r"\s*\d+")

# Page markers written by the PDF extractor, such as "Page 3:" at the start of a line.
_PAGE_MARKER = re.compile(r"^Page (\d+):", re.MULTILINE)


@dataclass(frozen=True)
class ChunkSpan:
    chunk_number: int
    start_char: int
    end_char: int
    text: str


@dataclass(frozen=True)
class _Unit:
    """The smallest piece kept whole: a sentence, a heading with its sentence, or a word-bounded piece."""

    start: int
    end: int
    paragraph: int


def chunk_text(
    content_text: str,
    max_chars: int = 1000,
    overlap_chars: int = 150,
) -> list[ChunkSpan]:
    """
    Return overlapping chunks of content_text, numbered from 1 in document order.

    Rules, applied in order:
    1. Text is not changed; only chunk boundaries move.
    2. Paragraphs split at blank lines, sentences at . ! ? followed by whitespace.
    3. Sentences are packed into chunks of at most max_chars. A paragraph is not
       split when it fits in one chunk.
    4. A short line without a full stop (a heading) stays with the text after it.
    5. Each new chunk repeats the last whole sentences of the previous one, up to
       overlap_chars, so ideas that cross a boundary appear whole in one chunk.
    6. A sentence longer than max_chars is cut at the last space before the limit.
    7. A tiny final chunk is merged into the one before it when that still fits.
    """
    # Security/correctness: the overlap must be smaller than the chunk, or the
    # window would never move forward and the loop could not finish.
    if max_chars < 1:
        raise ValueError("max_chars must be at least 1")
    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be at least 0 and smaller than max_chars")

    units = _units(content_text, max_chars)
    if not units:
        return []

    spans = _pack(units, max_chars, overlap_chars)
    spans = _merge_tiny_tail(spans, max_chars)
    return [
        ChunkSpan(
            chunk_number=number,
            start_char=start,
            end_char=end,
            text=content_text[start:end],
        )
        for number, (start, end) in enumerate(spans, start=1)
    ]


def page_number_at(content_text: str, offset: int) -> int | None:
    """
    The page a character belongs to, from the last "Page N:" marker before it.

    Analogy: the chapter heading you last passed while reading down the page.
    Returns None when the extractor wrote no page markers (for example, a plain text file).
    """
    page: int | None = None
    for marker in _PAGE_MARKER.finditer(content_text):
        if marker.start() > offset:
            break
        page = int(marker.group(1))
    return page


# --- Step 1: find the units ---------------------------------------------------


def _units(text: str, max_chars: int) -> list[_Unit]:
    units: list[_Unit] = []
    # A heading waits here until the paragraph after it is found, so the two stay together.
    pending: tuple[int, int] | None = None

    for index, (start, end) in enumerate(_paragraphs(text)):
        if _is_heading(text, start, end):
            pending = (start, end) if pending is None else (pending[0], end)
            continue

        sentences = _sentences(text, start, end)
        if pending is not None:
            sentences[0] = (pending[0], sentences[0][1])
            pending = None
        units.extend(_Unit(s, e, index) for s, e in sentences)

    # A heading at the very end has nothing after it, so it joins the text before it.
    if pending is not None:
        if units:
            last = units[-1]
            units[-1] = _Unit(last.start, pending[1], last.paragraph)
        else:
            units.append(_Unit(pending[0], pending[1], 0))

    return [piece for unit in units for piece in _split_oversized(text, unit, max_chars)]


def _paragraphs(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    position = 0
    for blank in _BLANK_LINE.finditer(text):
        span = _trim(text, position, blank.start())
        if span is not None:
            spans.append(span)
        position = blank.end()
    span = _trim(text, position, len(text))
    if span is not None:
        spans.append(span)
    return spans


def _is_heading(text: str, start: int, end: int) -> bool:
    line = text[start:end]
    return "\n" not in line and len(line) <= HEADING_MAX_CHARS and line[-1] not in ".!?"


def _sentences(text: str, start: int, end: int) -> list[tuple[int, int]]:
    cuts: list[int] = []
    for match in _SENTENCE_END.finditer(text, start, end):
        line_start = max(start, text.rfind("\n", start, match.start()) + 1)
        if _LIST_NUMBER.fullmatch(text[line_start : match.start()]):
            continue
        cuts.append(match.end())

    spans: list[tuple[int, int]] = []
    position = start
    for cut in cuts:
        span = _trim(text, position, cut)
        if span is not None:
            spans.append(span)
        position = cut
    span = _trim(text, position, end)
    if span is not None:
        spans.append(span)
    return spans


def _split_oversized(text: str, unit: _Unit, max_chars: int) -> list[_Unit]:
    """
    Cut a sentence longer than max_chars at the last space before the limit.

    Correctness: a cut only ever happens on whitespace, so no word is split. A single
    word longer than max_chars has no space to cut at, so it is cut at the limit.
    """
    pieces: list[_Unit] = []
    start = unit.start
    while unit.end - start > max_chars:
        limit = start + max_chars
        space = _last_space(text, start, limit)
        if space == -1:
            piece_end = limit
            next_start = limit
        else:
            piece_end = space
            while piece_end > start and text[piece_end - 1].isspace():
                piece_end -= 1
            next_start = space
        pieces.append(_Unit(start, piece_end, unit.paragraph))
        start = _skip_space(text, next_start, unit.end)
    pieces.append(_Unit(start, unit.end, unit.paragraph))
    return pieces


# --- Step 2: pack units into chunks -------------------------------------------


def _pack(units: list[_Unit], max_chars: int, overlap_chars: int) -> list[tuple[int, int]]:
    """
    Walk the units in order and close a chunk whenever the next unit would not fit.

    A chunk is described by the indexes of its first and last unit. The first unit can
    be an overlap unit carried over from the previous chunk.
    """
    groups: list[tuple[int, int]] = []
    first = 0
    last = 0

    for k in range(1, len(units)):
        if units[k].paragraph != units[k - 1].paragraph:
            block_last = _last_of_paragraph(units, k)
            # A paragraph that fits in one chunk must start a chunk together, not be split.
            block = block_last if units[block_last].end - units[k].start <= max_chars else k
        else:
            block = k

        if units[block].end - units[first].start <= max_chars:
            last = k
            continue

        groups.append((first, last))
        first = _overlap_start(units, first, last, block, k, max_chars, overlap_chars)
        last = k

    groups.append((first, last))
    return [(units[a].start, units[b].end) for a, b in groups]


def _overlap_start(
    units: list[_Unit],
    first: int,
    last: int,
    block: int,
    trigger: int,
    max_chars: int,
    overlap_chars: int,
) -> int:
    """
    Pick the first unit of the next chunk: the earliest unit of the old chunk that keeps
    the overlap within overlap_chars and still lets the new chunk hold the whole block.

    Analogy: when you start a new page, you copy the last few lines of the previous one
    to give the reader context, but only as many lines as fit the margin.
    """
    target_end = units[block].end
    for candidate in range(first + 1, last + 1):
        shared = units[last].end - units[candidate].start
        if shared <= overlap_chars and target_end - units[candidate].start <= max_chars:
            return candidate
    return trigger


def _merge_tiny_tail(spans: list[tuple[int, int]], max_chars: int) -> list[tuple[int, int]]:
    if len(spans) < 2:
        return spans
    (previous_start, _), (tail_start, tail_end) = spans[-2], spans[-1]
    if tail_end - tail_start < TINY_TAIL_CHARS and tail_end - previous_start <= max_chars:
        return [*spans[:-2], (previous_start, tail_end)]
    return spans


# --- small helpers -------------------------------------------------------------


def _last_of_paragraph(units: list[_Unit], index: int) -> int:
    last = index
    while last + 1 < len(units) and units[last + 1].paragraph == units[index].paragraph:
        last += 1
    return last


def _trim(text: str, start: int, end: int) -> tuple[int, int] | None:
    """Move both ends inward past whitespace, so a span starts and ends on real characters."""
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return (start, end) if start < end else None


def _last_space(text: str, start: int, limit: int) -> int:
    for index in range(min(limit, len(text) - 1), start, -1):
        if text[index].isspace():
            return index
    return -1


def _skip_space(text: str, index: int, end: int) -> int:
    while index < end and text[index].isspace():
        index += 1
    return index
