"""Step 0.9: turn the manuscript's endnotes into draft Codex entries.

Reads word/endnotes.xml from book/The Twice Born.docx. Paragraphs become
Markdown paragraphs, Word tables become Markdown tables, and embedded images
(EMF diagrams the browser can't show) become a TODO pointing at the matching
images/artifacts diagram. Each draft also records the manuscript sentence the
endnote is attached to, so find_page.py can locate it in the comic.

Output: src/content/codex/_drafts/NN-<slug>.md  (draft: true; edit, then move up)
Usage: python extract_endnotes.py
"""
import re
import zipfile
import xml.etree.ElementTree as ET

from common import BOOK_DIR, SITE

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DOCX = BOOK_DIR / "The Twice Born.docx"
OUT = SITE / "src" / "content" / "codex" / "_drafts"

# Titles for the 13 endnotes, in order (the notes themselves have no headings).
TITLES = [
    "Vaastu Purusha Mandala", "Ashtadhyayi", "The Vedic Mathematics shloka",
    "Dikpalas", "Lakshmi's symbol", "Nakshatras", "Stages of Shaivite renunciation",
    "Chakras and tattvas", "Kanchukas", "Bija mantras", "Periodic Table of the Tattvas",
    "Navagrahas and Navratnas", "Gnomon",
]


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def text_of(el: ET.Element) -> str:
    return re.sub(r"\s+", " ", "".join(t.text or "" for t in el.iter(f"{W}t"))).strip()


def table_md(tbl: ET.Element) -> str:
    rows = [[text_of(c).replace("|", "/") for c in tr.findall(f"{W}tc")] for tr in tbl.findall(f"{W}tr")]
    rows = [r for r in rows if any(r)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(lines)


def note_body(note: ET.Element) -> str:
    parts = []
    for child in note:
        if child.tag == f"{W}p":
            has_image = any(el.tag.endswith("}drawing") or el.tag.endswith("}pict") for el in child.iter())
            t = text_of(child)
            if t:
                parts.append(t)
            if has_image:
                parts.append("<!-- TODO: diagram in the manuscript (EMF); use the matching images/artifacts image -->")
        elif child.tag == f"{W}tbl":
            parts.append(table_md(child))
    return "\n\n".join(p for p in parts if p)


def anchors(doc_xml: str) -> dict[str, str]:
    """endnote id -> the sentence it is attached to in the manuscript."""
    root = ET.fromstring(doc_xml)
    out = {}
    for p in root.iter(f"{W}p"):
        refs = [r.get(f"{W}id") for r in p.iter(f"{W}endnoteReference")]
        if refs:
            para = text_of(p)
            for rid in refs:
                out[rid] = para[-240:]
    return out


def main() -> None:
    with zipfile.ZipFile(DOCX) as z:
        notes_xml = z.read("word/endnotes.xml")
        doc_xml = z.read("word/document.xml").decode("utf-8")
    where = anchors(doc_xml)
    notes = [n for n in ET.fromstring(notes_xml).findall(f"{W}endnote")
             if n.get(f"{W}type") not in ("separator", "continuationSeparator") and text_of(n)]
    OUT.mkdir(parents=True, exist_ok=True)
    for i, (note, title) in enumerate(zip(notes, TITLES), start=1):
        slug = slugify(title)
        body = note_body(note)
        anchor = where.get(note.get(f"{W}id"), "").replace('"', "'")
        front = (f"---\nid: {slug}\ntitle: \"{title}\"\ndraft: true\nsource: endnote-{i}\n"
                 f"summary: \"\"\nrelated: []\nfirstSeen: null  # fill with find_page.py using manuscriptAnchor\n"
                 f"manuscriptAnchor: \"{anchor}\"\n---\n\n")
        (OUT / f"{i:02d}-{slug}.md").write_text(front + body + "\n", encoding="utf-8")
        print(f"{i:02d} {title:34s} {len(body.split()):4d} words  tables={body.count(chr(10) + '|---')}")
    if len(notes) != len(TITLES):
        print(f"WARNING: {len(notes)} endnotes found, {len(TITLES)} titles defined")


if __name__ == "__main__":
    main()
