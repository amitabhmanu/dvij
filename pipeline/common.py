"""Shared paths and helpers for the Twice Born content pipeline."""
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
ROOT = SITE.parent
BOOK_DIR = ROOT / "book"
IMAGES_DIR = ROOT / "images"
ASSETS = ROOT / "site-assets"
REPORTS = SITE / "pipeline" / "reports"

# "parts" = page counts of the part PDFs (images/book N/BNC1..C5.pdf), whose
# concatenation is exactly the book PDF.
BOOKS = {
    1: {"slug": "b1", "title": "Valley", "pages": 42, "parts": [12, 8, 6, 9, 7]},
    2: {"slug": "b2", "title": "Parchment", "pages": 34, "parts": [5, 7, 8, 6, 8]},
    3: {"slug": "b3", "title": "Leaf", "pages": 34, "parts": [9, 7, 7, 6, 5]},
    4: {"slug": "b4", "title": "Ascent", "pages": 32, "parts": [8, 9, 9, 6]},
    5: {"slug": "b5", "title": "Discovery", "pages": 29, "parts": [6, 7, 6, 5, 5]},
}


def source_pdf(book: int) -> Path:
    return BOOK_DIR / f"B{book}.pdf"


def compressed_pdf(book: int) -> Path:
    return ASSETS / "pdf" / f"the-twice-born-b{book}.pdf"


def parse_books(arg: str | None) -> list[int]:
    """'1,3' -> [1, 3]; None or 'all' -> every book."""
    if not arg or arg == "all":
        return list(BOOKS)
    return [int(b) for b in arg.split(",")]
