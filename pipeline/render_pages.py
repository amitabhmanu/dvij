"""Step 0.2: render every page of the compressed PDFs to a 2x PNG master.

Masters stay local (site-assets/master/) and feed make_variants.mjs.
Usage: python render_pages.py [--books 1,2] [--force]
"""
import argparse

import fitz

from common import ASSETS, BOOKS, compressed_pdf, parse_books

ZOOM = 2.0  # 1058x1688 pt page -> 2116x3376 px


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--books")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    out_dir = ASSETS / "master"
    out_dir.mkdir(parents=True, exist_ok=True)
    for book in parse_books(args.books):
        doc = fitz.open(compressed_pdf(book))
        slug = BOOKS[book]["slug"]
        rendered = 0
        for i, page in enumerate(doc, start=1):
            target = out_dir / f"{slug}-p{i:03d}.png"
            if target.exists() and not args.force:
                continue
            page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), alpha=False).save(target)
            rendered += 1
        print(f"B{book}: {doc.page_count} pages, {rendered} rendered")


if __name__ == "__main__":
    main()
