#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional, Union

from docx import Document
from docx.oxml.ns import qn
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph
from lxml import etree


DOCX_PATH_DEFAULT = Path("/Users/jingruiguo/Desktop/Physik Mitschrift.docx")


GERMAN_MAP = {
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",
    "Ä": "Ae",
    "Ö": "Oe",
    "Ü": "Ue",
    "ß": "ss",
}


def transliterate(s: str) -> str:
    return "".join(GERMAN_MAP.get(ch, ch) for ch in s)


_num_prefix_re = re.compile(r"^\s*\d+(?:\.\d+)*\s*")


def _to_words(title: str) -> list[str]:
    t = _num_prefix_re.sub("", title)
    t = transliterate(t)
    parts = re.split(r"[^0-9A-Za-z]+", t)
    return [p for p in parts if p]


def lower_camel(title: str) -> str:
    words = _to_words(title)
    if not words:
        return "note"
    first = words[0].lower()
    rest = [w.capitalize() for w in words[1:]]
    return first + "".join(rest)


def chapter_folder_name(chapter_title: str, idx: int) -> str:
    return f"{idx:02d}_{lower_camel(chapter_title)}"


def iter_block_items(doc: Document) -> Iterator[Union[Paragraph, Table]]:
    body = doc.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)


def table_to_md(table: Table) -> list[str]:
    rows: list[list[str]] = []
    max_cols = 0
    for row in table.rows:
        cols: list[str] = []
        for cell in row.cells:
            text = (cell.text or "").strip()
            text = re.sub(r"\s+\n\s+", "<br>", text)
            text = text.replace("\n", "<br>")
            cols.append(text)
        max_cols = max(max_cols, len(cols))
        rows.append(cols)
    if not rows:
        return []

    for r in rows:
        if len(r) < max_cols:
            r.extend([""] * (max_cols - len(r)))

    def esc(v: str) -> str:
        return (v or "").replace("|", "\\|")

    header = rows[0]
    lines: list[str] = []
    lines.append("| " + " | ".join(esc(v) for v in header) + " |")
    lines.append("| " + " | ".join(["---"] * max_cols) + " |")
    for r in rows[1:]:
        lines.append("| " + " | ".join(esc(v) for v in r) + " |")
    return lines


def write_md(path: Path, frontmatter: dict, body_lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    def yaml_str(s: str) -> str:
        s = s.replace("\\", "\\\\").replace('"', '\\"')
        return f"\"{s}\""

    fm_lines = ["---"]
    for k, v in frontmatter.items():
        if isinstance(v, list):
            fm_lines.append(f"{k}:")
            for item in v:
                fm_lines.append(f"  - {yaml_str(str(item))}")
        else:
            if isinstance(v, str):
                fm_lines.append(f"{k}: {yaml_str(v)}")
            else:
                fm_lines.append(f"{k}: {v}")
    fm_lines.append("---")
    content = "\n".join(fm_lines) + "\n\n" + "\n".join(body_lines).rstrip() + "\n"
    path.write_text(content, encoding="utf-8")


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def omml_to_latex(el: etree._Element) -> str:
    tag = etree.QName(el).localname

    def child_one(name: str) -> Optional[etree._Element]:
        found = el.find(f"m:{name}", namespaces=NS)
        return found

    def children(name: str) -> list[etree._Element]:
        return el.findall(f"m:{name}", namespaces=NS)

    def norm_math_text(s: str) -> str:
        # Word sometimes inserts special unicode symbols that KaTeX/LaTeX don't like.
        return (
            (s or "")
            .replace("⁡", "")  # function application
            .replace("%", r"\%")
            .replace("∊", r"\in")
            .replace("∈", r"\in")
            .replace("⋅", r"\cdot ")
            .replace("·", r"\cdot ")
            .replace("×", r"\times ")
            .replace("−", "-")
        )

    if tag == "t":
        return norm_math_text(el.text or "")
    if tag == "r":
        ts = el.xpath(".//m:t/text()", namespaces=NS)
        return norm_math_text("".join(ts))

    if tag in ("oMath", "oMathPara"):
        parts = []
        for c in el.xpath("./*", namespaces=NS):
            parts.append(omml_to_latex(c))
        return "".join(parts)

    if tag == "f":
        num = child_one("num")
        den = child_one("den")
        num_s = omml_to_latex(num) if num is not None else ""
        den_s = omml_to_latex(den) if den is not None else ""
        return rf"\frac{{{num_s}}}{{{den_s}}}"

    if tag == "sSub":
        e = child_one("e")
        sub = child_one("sub")
        return rf"{omml_to_latex(e) if e is not None else ''}_{{{omml_to_latex(sub) if sub is not None else ''}}}"

    if tag == "sSup":
        e = child_one("e")
        sup = child_one("sup")
        return rf"{omml_to_latex(e) if e is not None else ''}^{{{omml_to_latex(sup) if sup is not None else ''}}}"

    if tag == "sSubSup":
        e = child_one("e")
        sub = child_one("sub")
        sup = child_one("sup")
        base = omml_to_latex(e) if e is not None else ""
        return rf"{base}_{{{omml_to_latex(sub) if sub is not None else ''}}}^{{{omml_to_latex(sup) if sup is not None else ''}}}"

    if tag == "rad":
        deg = child_one("deg")
        e = child_one("e")
        if deg is not None and (deg_text := omml_to_latex(deg)).strip():
            return rf"\sqrt[{deg_text}]{{{omml_to_latex(e) if e is not None else ''}}}"
        return rf"\sqrt{{{omml_to_latex(e) if e is not None else ''}}}"

    if tag == "acc":
        acc_pr = child_one("accPr")
        chr_ = None
        if acc_pr is not None:
            chr_el = acc_pr.find("m:chr", namespaces=NS)
            if chr_el is not None:
                chr_ = chr_el.get(qn("m:val")) or chr_el.get("m:val")
        e = child_one("e")
        inner = omml_to_latex(e) if e is not None else ""
        if chr_ in ("˙", "."):
            return rf"\dot{{{inner}}}"
        if chr_ in ("¨",):
            return rf"\ddot{{{inner}}}"
        if chr_ in ("¯", "‾", "̄"):
            return rf"\bar{{{inner}}}"
        if chr_ in ("~", "˜"):
            return rf"\tilde{{{inner}}}"
        if chr_ in ("^", "ˆ"):
            return rf"\hat{{{inner}}}"
        return inner

    if tag == "d":
        # Delimiter (parentheses / brackets)
        e = child_one("e")
        inner = omml_to_latex(e) if e is not None else ""
        return rf"\left({inner}\right)"

    if tag == "nary":
        nary_pr = child_one("naryPr")
        op = r"\int"
        if nary_pr is not None:
            chr_el = nary_pr.find("m:chr", namespaces=NS)
            if chr_el is not None:
                val = chr_el.get(qn("m:val")) or chr_el.get("m:val")
                if val in ("∑",):
                    op = r"\sum"
                elif val in ("∏",):
                    op = r"\prod"
                elif val in ("⋂",):
                    op = r"\bigcap"
                elif val in ("⋃",):
                    op = r"\bigcup"
                elif val in ("∫", "∮", "∯", "∰"):
                    op = val
        sub = child_one("sub")
        sup = child_one("sup")
        e = child_one("e")
        sub_s = omml_to_latex(sub) if sub is not None else ""
        sup_s = omml_to_latex(sup) if sup is not None else ""
        limits = ""
        if sub_s.strip():
            limits += rf"_{{{sub_s}}}"
        if sup_s.strip():
            limits += rf"^{{{sup_s}}}"
        inner = omml_to_latex(e) if e is not None else ""
        return f"{op}{limits} {inner}"

    # Fallback: concatenate children
    parts = []
    for c in el.xpath("./*", namespaces=NS):
        parts.append(omml_to_latex(c))
    return "".join(parts)


def paragraph_to_text_with_math(para: Paragraph) -> str:
    xml = para._element.xml
    root = etree.fromstring(xml.encode("utf-8"))
    out: list[str] = []

    def run_props_md(run_el: etree._Element) -> tuple[bool, bool, bool]:
        rpr = run_el.find("w:rPr", namespaces=NS)
        if rpr is None:
            return False, False, False

        bold = rpr.find("w:b", namespaces=NS) is not None

        underline = False
        u = rpr.find("w:u", namespaces=NS)
        if u is not None:
            val = u.get(qn("w:val")) or u.get("w:val")
            underline = (val or "").lower() not in ("none", "0", "false")

        highlight = rpr.find("w:highlight", namespaces=NS) is not None
        return bold, underline, highlight

    def run_text(run_el: etree._Element) -> str:
        parts: list[str] = []
        for n in run_el.iter():
            local = etree.QName(n).localname
            ns = etree.QName(n).namespace
            if ns != NS["w"]:
                continue
            if local == "t":
                parts.append(n.text or "")
            elif local == "tab":
                parts.append("\t")
            elif local in ("br", "cr"):
                parts.append("\n")
        return "".join(parts)

    def apply_md_wrappers(s: str, bold: bool, underline: bool, highlight: bool) -> str:
        if not s:
            return s
        if s.isspace():
            return s

        # Keep wrapping local to each line to avoid spanning markdown across line breaks.
        lines = s.split("\n")
        wrapped_lines: list[str] = []
        for ln in lines:
            if not ln:
                wrapped_lines.append(ln)
                continue
            w = ln
            if underline or highlight:
                w = f"=={w}=="
            if bold:
                w = f"**{w}**"
            wrapped_lines.append(w)
        return "\n".join(wrapped_lines)

    for child in root:
        local = etree.QName(child).localname
        ns = etree.QName(child).namespace
        if ns == NS["w"] and local == "r":
            seg = run_text(child)
            bold, underline, highlight = run_props_md(child)
            out.append(apply_md_wrappers(seg, bold=bold, underline=underline, highlight=highlight))
        elif ns == NS["w"] and local in ("br", "cr"):
            out.append("\n")
        elif ns == NS["m"] and local in ("oMath", "oMathPara"):
            latex = omml_to_latex(child).strip()
            if latex:
                out.append(f"${latex}$")
        else:
            # ignore other nodes here (e.g., properties)
            continue
    s = "".join(out).replace("\u00a0", " ")
    # Merge adjacent segments that ended up double-wrapped due to run boundaries.
    s = s.replace("****", "")
    s = s.replace("====", "")
    return s.strip()


_definition_re = re.compile(
    r"^(?P<term>[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß0-9/ -]{0,32}):\s*(?P<rest>.+)$"
)


def format_text_lines(text: str) -> list[str]:
    raw_lines = text.splitlines() if "\n" in text else [text]
    lines = [ln.strip() for ln in raw_lines if ln.strip() != ""]
    if not lines:
        return []

    if len(lines) == 1:
        # Short standalone labels: make them stand out.
        if (
            len(lines[0]) <= 48
            and not any(ch in lines[0] for ch in ".!?")
            and " " not in lines[0].strip()
            and lines[0].strip() == lines[0]
            and not lines[0].startswith(("**", "=="))
        ):
            lines = [f"**{lines[0]}**"]

        m = _definition_re.match(lines[0])
        if m:
            term = m.group("term").strip()
            rest = m.group("rest").strip()
            if term and rest and not term[0].isdigit() and len(term.split()) <= 2:
                lines = [f"**{term}**: {rest}"]

    out: list[str] = []
    for ln in lines:
        if ln.startswith(("#", "-", "!", "|")):
            out.append(ln)
            continue
        if math := standalone_math(ln):
            out.extend(["$$", math, "$$"])
            continue

        if (
            len(ln) <= 140
            and not ln.startswith(("**", "=="))
            and re.search(r"\b(Annahme|vereinfach|Voraussetzung)\b", ln, flags=re.IGNORECASE)
        ):
            ln = f"=={ln}=="

        out.append(f"{ln}  ")
    return out


def standalone_math(line: str) -> Optional[str]:
    stripped = line.strip()
    wrappers = [
        ("**$", "$**"),
        ("==$", "$=="),
        ("$","$"),
    ]
    for prefix, suffix in wrappers:
        if stripped.startswith(prefix) and stripped.endswith(suffix) and len(stripped) > len(prefix) + len(suffix):
            inner = stripped[len(prefix) : len(stripped) - len(suffix)].strip()
            text_without_commands = re.sub(r"\\[A-Za-z]+", "", inner)
            words = re.findall(r"[A-Za-zÄÖÜäöüß]{4,}", text_without_commands)
            has_explanatory_words = any(word.lower() not in {"konstant", "const"} for word in words)
            if "$" not in inner and "\n" not in inner and not has_explanatory_words:
                return inner
    return None


def emphasize_core_statements(lines: list[str]) -> list[str]:
    out = list(lines)
    trigger = False
    for idx, line in enumerate(out):
        stripped = line.strip()
        if not stripped:
            continue

        if trigger:
            if stripped.startswith("(") and stripped.endswith(")") and len(stripped) <= 80:
                continue
            if (
                not stripped.startswith(("#", "!", "|", "$$", "$", "**", "==", "-", "<"))
                and len(stripped.rstrip("  ")) <= 280
            ):
                bare = stripped.rstrip("  ")
                suffix = "  " if stripped.endswith("  ") else ""
                out[idx] = f"**{bare}**{suffix}"
                trigger = False
                continue
            if stripped.startswith(("!", "$$", "|")):
                continue
            trigger = False

        if re.search(r"\b(Gesetz|Axiom|Prinzip|Satz)\b", stripped):
            if stripped.startswith("##") or (stripped.startswith("**") and stripped.endswith("**") and len(stripped) <= 84):
                trigger = True
                continue

        if (
            len(stripped) <= 160
            and not stripped.startswith(("**", "==", "#", "-", "!", "|", "$$", "<"))
            and re.search(r"\b(Annahme|Voraussetzung|im Gleichgewicht gilt)\b", stripped, flags=re.IGNORECASE)
        ):
            bare = stripped.rstrip("  ")
            suffix = "  " if stripped.endswith("  ") else ""
            out[idx] = f"=={bare}=={suffix}"

    return out


def page_body(lines: list[str]) -> list[str]:
    body = ["<div v-pre>", ""]
    body.extend(emphasize_core_statements(lines))
    if body and body[-1] != "":
        body.append("")
    body.append("</div>")
    return body


def extract_images_from_paragraph(
    doc: Document, para: Paragraph, media_dir: Path, img_counter: list[int]
) -> list[tuple[str, str]]:
    out = []
    # python-docx's xpath wrapper doesn't accept the lxml `namespaces=` kwarg.
    # Use local-name matching to find embedded images.
    blips = para._element.xpath('.//*[local-name()="blip"]')
    for blip in blips:
        rId = blip.get(qn("r:embed"))
        if not rId:
            continue
        part = doc.part.related_parts.get(rId)
        if not part:
            continue
        content_type = getattr(part, "content_type", "") or ""
        ext = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/gif": ".gif",
            "image/bmp": ".bmp",
            "image/tiff": ".tiff",
            "image/x-emf": ".emf",
            "image/emf": ".emf",
            "image/x-wmf": ".wmf",
            "image/wmf": ".wmf",
            "image/svg+xml": ".svg",
        }.get(content_type, "")
        if not ext:
            name = getattr(part, "partname", None)
            ext = Path(str(name)).suffix if name else ".bin"
            if not ext:
                ext = ".bin"

        img_counter[0] += 1
        fname = f"img_{img_counter[0]:03d}{ext}"
        out_path = media_dir / fname
        if not out_path.exists():
            out_path.write_bytes(part.blob)
        out.append((fname, f"../media/physik_mitschrift/{fname}"))
    return out


@dataclass
class Section:
    title: str
    file: Path
    lines: list[str]


@dataclass
class Chapter:
    title: str
    folder: Path
    overview_file: Path
    overview_lines: list[str]
    sections: list[Section]


def import_docx(
    docx_path: Path,
    out_root: Path,
    media_dir: Path,
) -> tuple[list[Chapter], int]:
    doc = Document(str(docx_path))

    chapters: list[Chapter] = []
    current_chapter: Optional[Chapter] = None
    current_section: Optional[Section] = None
    section_idx = 0
    img_counter = [0]
    chapter_idx = 0
    started = False

    def ensure_target_lines() -> list[str]:
        if current_section is not None:
            return current_section.lines
        if current_chapter is not None:
            return current_chapter.overview_lines
        return []

    def flush_section() -> None:
        nonlocal current_section
        if current_chapter is None or current_section is None:
            return
        current_chapter.sections.append(current_section)
        current_section = None

    def flush_chapter() -> None:
        nonlocal current_chapter
        if current_chapter is None:
            return
        flush_section()
        chapters.append(current_chapter)
        current_chapter = None

    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            style = block.style.name if block.style else ""

            if not started:
                if style == "haupt" and paragraph_to_text_with_math(block):
                    started = True
                else:
                    continue

            if style in ("toc 1", "toc 2", "toc 3"):
                continue

            text = paragraph_to_text_with_math(block)

            if style == "haupt" and text:
                flush_chapter()
                chapter_idx += 1
                section_idx = 0
                folder = out_root / chapter_folder_name(text, chapter_idx)
                current_chapter = Chapter(
                    title=text,
                    folder=folder,
                    overview_file=folder / f"{folder.name}.md",
                    overview_lines=[],
                    sections=[],
                )
                continue

            if current_chapter is None:
                continue

            if style == "Unterpunkt 1" and text:
                flush_section()
                section_idx += 1
                filename = f"{section_idx:02d}_{lower_camel(text)}.md"
                current_section = Section(
                    title=text,
                    file=current_chapter.folder / filename,
                    lines=[],
                )
                continue

            images = extract_images_from_paragraph(doc, block, media_dir, img_counter)
            target_lines = ensure_target_lines()

            if style == "Unterpunkt" and text:
                target_lines.extend([f"## {text}", ""])
                continue

            if style == "Heading 2" and text:
                target_lines.extend([f"### {text}", ""])
                continue

            if style == "List Paragraph" and text:
                target_lines.append(f"- {text}")
                for _, rel in images:
                    target_lines.append(f"![img]({rel})")
                continue

            if text:
                target_lines.extend(format_text_lines(text))
                target_lines.append("")
            for _, rel in images:
                target_lines.extend([f"![img]({rel})", ""])

        else:
            if not started or current_chapter is None:
                continue
            md_lines = table_to_md(block)
            if not md_lines:
                continue
            target_lines = ensure_target_lines()
            target_lines.extend(["", *md_lines, ""])

    flush_chapter()
    return chapters, img_counter[0]


def main() -> None:
    out_root = Path("lecturenotes")
    media_dir = out_root / "media" / "physik_mitschrift"
    media_dir.mkdir(parents=True, exist_ok=True)

    docx_path = DOCX_PATH_DEFAULT
    chapters, img_count = import_docx(docx_path, out_root, media_dir)

    index_lines = []
    for ch in chapters:
        chap_rel = ch.overview_file.relative_to(out_root)
        index_lines.append(f"- [{ch.title}](./{chap_rel.as_posix()})")
    write_md(
        out_root / "index.md",
        {"title": "LECTURE NOTES"},
        index_lines + ["", "*Quelle*: Physik Mitschrift.docx"],
    )

    for ch in chapters:
        ch.folder.mkdir(parents=True, exist_ok=True)
        overview_lines: list[str] = []
        if ch.overview_lines:
            overview_lines.extend(ch.overview_lines)
            if overview_lines and overview_lines[-1] != "":
                overview_lines.append("")

        if ch.sections:
            overview_lines.extend(["## Inhalt", ""])
            for sec in ch.sections:
                sec_rel = sec.file.relative_to(ch.overview_file.parent)
                overview_lines.append(f"- [{sec.title}](./{sec_rel.as_posix()})")
            overview_lines.append("")

        write_md(
            ch.overview_file,
            {"title": ch.title, "tags": ["lecturenotes", "Physik Mitschrift"]},
            page_body(overview_lines),
        )

        for sec in ch.sections:
            write_md(
                sec.file,
                {"title": sec.title, "tags": ["lecturenotes", "Physik Mitschrift"]},
                page_body(sec.lines),
            )

    print(f"Chapters: {len(chapters)}")
    print(f"Images extracted: {img_count}")


if __name__ == "__main__":
    main()
