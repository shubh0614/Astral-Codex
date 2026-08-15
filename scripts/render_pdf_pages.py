"""
Render PDF pages to PNG for vision extraction.

usage: python scripts/render_pdf_pages.py <pdf> <outdir> [pages...]
       with no page list, prints a per-page table-likeness report
"""

import sys
from pathlib import Path

import pymupdf

DPI = 200


def report(doc):
    print(f"{doc.page_count} pages\n")
    for i, page in enumerate(doc, start=1):
        text = page.get_text()
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        numeric = sum(1 for l in lines if sum(c.isdigit() for c in l) / max(len(l), 1) > 0.3)
        has_tbl = "Table" in text
        print(
            f"  p{i:<3} lines={len(lines):<4} numeric_lines={numeric:<4} "
            f"{'TABLE-CAPTION' if has_tbl else ''}"
        )


def main():
    pdf = Path(sys.argv[1])
    doc = pymupdf.open(pdf)
    if len(sys.argv) < 4:
        report(doc)
        return
    outdir = Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    for p in sys.argv[3:]:
        n = int(p)
        pix = doc[n - 1].get_pixmap(dpi=DPI)
        out = outdir / f"{pdf.stem}_p{n:03d}.png"
        pix.save(out)
        print(f"{out}  ({pix.width}x{pix.height})")


if __name__ == "__main__":
    main()
