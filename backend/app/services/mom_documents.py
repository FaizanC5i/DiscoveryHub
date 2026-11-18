"""
Turns the agent's meeting output into a Word, Markdown or JSON document.

Analogy: a typesetter. The agent's answer is first read into a flat list of blocks (headings,
paragraphs, bullets, numbered items, label/value pairs, tables). Each output format then lays
out the same blocks, so the three downloads always carry the same content.
"""

import io
import json
import re
from datetime import datetime
from typing import Any

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

DOCUMENT_TITLES = {"mom": "Minutes of Meeting", "detailed-summary": "Detailed Meeting Explanation"}
NAVY = RGBColor(0x1F, 0x38, 0x64)
BLUE = RGBColor(0x2F, 0x54, 0x96)
GRAY = RGBColor(0x59, 0x59, 0x59)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BORDER = "BFBFBF"


def build_document(output: Any, body: Any, project_name: str | None, source_name: str | None,
                   document_type: str) -> dict:
    """The parts every format needs: title, subtitle line, and blocks."""
    stamp = datetime.now().strftime("%d %b %Y, %H:%M")
    name = project_name or _source_stem(source_name)
    return {
        "title": DOCUMENT_TITLES[document_type],
        "project_name": name,
        "meta_line": f"Generated: {stamp}",
        "blocks": make_blocks(body, DOCUMENT_TITLES[document_type]),
        "output": output,
    }


def to_markdown(doc: dict) -> str:
    lines = [f"# {doc['title']}"]
    if doc["project_name"]:
        lines.append(f"**{doc['project_name']}**")
    lines += [f"_{doc['meta_line']}_", ""]

    for block in doc["blocks"]:
        kind = block[0]
        if kind == "heading":
            lines += ["", "#" * (block[1] + 1) + " " + block[2], ""]
        elif kind == "para":
            lines += [block[1], ""]
        elif kind == "bullet":
            lines.append(("  " if block[2] > 1 else "") + "- " + block[1])
        elif kind == "number":
            lines.append(f"{block[1]}. {block[2]}")
        elif kind == "labelvalue":
            lines.append(f"**{block[1]}:** {block[2]}  ")
        elif kind == "table":
            headers, rows = block[1], block[2]
            lines += ["", "| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
            for row in rows:
                padded = list(row) + [""] * (len(headers) - len(row))
                lines.append("| " + " | ".join(padded[: len(headers)]) + " |")
            lines.append("")
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def to_json(doc: dict) -> bytes:
    return json.dumps(doc["output"], indent=2, ensure_ascii=False, default=str).encode("utf-8")


def to_docx(doc: dict) -> bytes:
    document = Document()
    _setup_styles(document)
    _setup_page(document, doc["project_name"] or doc["title"])

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(doc["title"].upper())
    run.bold = True
    run.font.size = Pt(20)
    run.font.color.rgb = NAVY
    if doc["project_name"]:
        project = document.add_paragraph()
        project.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = project.add_run(doc["project_name"])
        run.bold = True
        run.font.size = Pt(12)
        run.font.color.rgb = BLUE
    meta = document.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = meta.add_run(doc["meta_line"])
    run.font.size = Pt(9)
    run.font.color.rgb = GRAY

    for block in doc["blocks"]:
        kind = block[0]
        if kind == "heading":
            document.add_heading(block[2], level=block[1])
        elif kind == "para":
            _add_runs(document.add_paragraph(), block[1])
        elif kind == "bullet":
            _add_runs(document.add_paragraph(style="List Bullet 2" if block[2] > 1 else "List Bullet"), block[1])
        elif kind == "number":
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.left_indent = Cm(0.9)
            paragraph.paragraph_format.first_line_indent = Cm(-0.6)
            _add_runs(paragraph, f"{block[1]}.  {block[2]}")
        elif kind == "labelvalue":
            paragraph = document.add_paragraph()
            paragraph.add_run(block[1] + ": ").bold = True
            _add_runs(paragraph, block[2])
        elif kind == "table":
            _add_table(document, block[1], block[2])

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _source_stem(source_name: str | None) -> str:
    if not source_name:
        return ""
    stem = re.sub(r"\.[A-Za-z0-9]+$", "", source_name)
    return re.sub(r"\s+", " ", stem.replace("_", " ")).strip()


def pretty_key(key: Any) -> str:
    text = str(key).strip()
    number = re.match(r"^(\d+)[_\-\s]+(.*)$", text)
    prefix = ""
    if number:
        prefix = number.group(1) + ". "
        text = number.group(2)
    return prefix + " ".join(word.capitalize() for word in re.sub(r"[_\-]+", " ", text).split())


def _scalar_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value).strip()


def _flat_text(value: Any) -> str:
    if value is None or isinstance(value, (str, int, float, bool)):
        return _scalar_text(value)
    if isinstance(value, list):
        return "; ".join(text for text in (_flat_text(item) for item in value) if text)
    if isinstance(value, dict):
        parts = [f"{pretty_key(k)}: {_flat_text(v)}" for k, v in value.items()]
        return "; ".join(part for part in parts if not part.endswith(": "))
    return str(value)


def _clean_heading(text: str) -> str:
    return re.sub(r"\s*#+\s*$", "", text.strip()).replace("**", "").strip()


def _plain_heading(lines: list[str], index: int) -> tuple[int, str] | None:
    """Plain-text headings such as '1. Overview' or '4.1 Topic' on their own line."""
    text = lines[index].strip()
    match = re.match(r"^(\d{1,2})(\.\d{1,2})?[.)]?\s+([A-Z0-9].{1,95})$", text)
    if not match or text.endswith((".", ":", ";", ",")):
        return None
    before_blank = index == 0 or not lines[index - 1].strip()
    after_blank = index == len(lines) - 1 or not lines[index + 1].strip()
    if not (before_blank and after_blank):
        return None
    return (4 if match.group(2) else 3), _clean_heading(text)


def text_to_blocks(text: str) -> list[tuple]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[tuple] = []
    table_lines: list[str] = []

    def flush_table() -> None:
        if not table_lines:
            return
        rows = []
        for line in table_lines:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            rows.append(cells)
        if len(rows) >= 2:
            blocks.append(("table", rows[0], rows[1:]))
        else:
            blocks.extend(("para", " | ".join(row)) for row in rows)
        table_lines.clear()

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("|"):
            table_lines.append(stripped)
            continue
        flush_table()
        if not stripped or re.fullmatch(r"[-*_]{3,}", stripped):
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            blocks.append(("heading", len(heading.group(1)), _clean_heading(heading.group(2))))
            continue
        plain = _plain_heading(lines, index)
        if plain:
            blocks.append(("heading", plain[0], plain[1]))
            continue
        bullet = re.match(r"^(\s*)[-*•]\s+(.*)$", line)
        if bullet:
            depth = 2 if len(bullet.group(1)) >= 2 else 1
            blocks.append(("bullet", bullet.group(2).strip(), depth))
            continue
        number = re.match(r"^\s*(\d+)[.)]\s+(.*)$", line)
        if number:
            blocks.append(("number", int(number.group(1)), number.group(2).strip()))
            continue
        blocks.append(("para", stripped))
    flush_table()
    return blocks


def build_blocks(value: Any, level: int = 3) -> list[tuple]:
    if isinstance(value, str):
        return text_to_blocks(value)

    blocks: list[tuple] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if item is None or isinstance(item, (str, int, float, bool)):
                text = _scalar_text(item)
                if not text:
                    continue
                if isinstance(item, str) and ("\n" in text or len(text) > 300):
                    blocks.append(("heading", level, pretty_key(key)))
                    blocks.extend(text_to_blocks(text))
                else:
                    blocks.append(("labelvalue", pretty_key(key), text))
            else:
                blocks.append(("heading", level, pretty_key(key)))
                blocks.extend(build_blocks(item, level + 1))
        return blocks

    if isinstance(value, list):
        if not value:
            return blocks
        if all(isinstance(item, dict) for item in value):
            headers: list[str] = []
            for item in value:
                for key in item:
                    if key not in headers:
                        headers.append(key)
            if 0 < len(headers) <= 6:
                rows = [[_flat_text(item.get(h, "")) for h in headers] for item in value]
                blocks.append(("table", [pretty_key(h) for h in headers], rows))
            else:
                for index, item in enumerate(value, start=1):
                    blocks.append(("heading", level, f"Item {index}"))
                    blocks.extend(build_blocks(item, level + 1))
            return blocks
        blocks.extend(("bullet", text, 1) for text in (_flat_text(item) for item in value) if text)
        return blocks

    text = _scalar_text(value)
    if text:
        blocks.append(("para", text))
    return blocks


def make_blocks(body: Any, doc_title: str) -> list[tuple]:
    """Build blocks, drop a heading that repeats the document title, and cap heading levels at 3."""
    blocks = build_blocks(body)
    if blocks and blocks[0][0] == "heading" and blocks[0][1] == 1 and re.search(
        r"minutes of meeting|meeting minutes|detailed|explanation|summary", blocks[0][2], re.I
    ):
        blocks = blocks[1:]
    levels = sorted({b[1] for b in blocks if b[0] == "heading"})
    mapping = {level: min(rank + 1, 3) for rank, level in enumerate(levels)}
    return [("heading", mapping[b[1]], b[2]) if b[0] == "heading" else b for b in blocks]


def _add_runs(paragraph, text: str) -> None:
    """Write text, honouring **bold** markers."""
    for part in re.split(r"(\*\*[^*]+\*\*)", text):
        if not part:
            continue
        is_bold = len(part) > 4 and part.startswith("**") and part.endswith("**")
        paragraph.add_run(part[2:-2] if is_bold else part).bold = is_bold


def _setup_styles(document) -> None:
    normal = document.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(6)
    for name, size, color in (("Heading 1", 14, NAVY), ("Heading 2", 12, BLUE), ("Heading 3", 11, BLUE)):
        style = document.styles[name]
        style.font.name = "Calibri"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = color
        style.paragraph_format.keep_with_next = True


def _add_field(paragraph, instruction: str) -> None:
    def run_with(element):
        run = paragraph.add_run()
        run.font.size = Pt(8.5)
        run.font.color.rgb = GRAY
        run._r.append(element)

    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    run_with(begin)
    code = OxmlElement("w:instrText")
    code.set(qn("xml:space"), "preserve")
    code.text = f" {instruction} "
    run_with(code)
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    run_with(separate)
    shown = OxmlElement("w:t")
    shown.text = "1"
    run_with(shown)
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run_with(end)


def _setup_page(document, header_text: str) -> None:
    section = document.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = section.right_margin = Cm(2)
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2)

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = header.add_run(header_text[:100])
    run.font.size = Pt(8.5)
    run.font.color.rgb = GRAY

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    label = footer.add_run("Page ")
    label.font.size = Pt(8.5)
    label.font.color.rgb = GRAY
    _add_field(footer, "PAGE")
    middle = footer.add_run(" of ")
    middle.font.size = Pt(8.5)
    middle.font.color.rgb = GRAY
    _add_field(footer, "NUMPAGES")


def _style_cell(cell, fill: str | None = None) -> None:
    properties = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), BORDER)
        borders.append(element)
    properties.append(borders)
    if fill:
        shading = OxmlElement("w:shd")
        shading.set(qn("w:val"), "clear")
        shading.set(qn("w:color"), "auto")
        shading.set(qn("w:fill"), fill)
        properties.append(shading)


def _write_cell(cell, text: str, bold: bool = False, color: RGBColor | None = None) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_before = Pt(2)
    paragraph.paragraph_format.space_after = Pt(2)
    for part in re.split(r"(\*\*[^*]+\*\*)", text):
        if not part:
            continue
        is_bold = len(part) > 4 and part.startswith("**") and part.endswith("**")
        run = paragraph.add_run(part[2:-2] if is_bold else part)
        run.font.size = Pt(9.5)
        run.bold = bold or is_bold
        if color:
            run.font.color.rgb = color


def _add_table(document, headers: list[str], rows: list[list[str]]) -> None:
    columns = len(headers)
    table = document.add_table(rows=1, cols=columns)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    header_row = table.rows[0]
    marker = OxmlElement("w:tblHeader")
    marker.set(qn("w:val"), "true")
    header_row._tr.get_or_add_trPr().append(marker)
    for index, header in enumerate(headers):
        cell = header_row.cells[index]
        _write_cell(cell, header, bold=True, color=WHITE)
        _style_cell(cell, fill="1F3864")

    for number, row in enumerate(rows):
        new_row = table.add_row()
        split = OxmlElement("w:cantSplit")
        split.set(qn("w:val"), "true")
        new_row._tr.get_or_add_trPr().append(split)
        for index in range(columns):
            cell = new_row.cells[index]
            _write_cell(cell, row[index] if index < len(row) else "")
            _style_cell(cell, fill="F2F5FA" if number % 2 else None)

    spacer = document.add_paragraph()
    spacer.paragraph_format.space_after = Pt(4)
