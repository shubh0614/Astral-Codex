"""
Fetch the Roman, Vedic and Maya raw sources for the Phase 0 sample.

All three are single-file fetches, unlike Babylonian which needs a scraper.
Stores raw and unmodified under data/raw/<tradition>/.

Roman  -- Julius Obsequens, Liber Prodigiorum, attalus.org translation.
Vedic  -- Brihat Samhita, Panditabhushana V. Subrahmanya Sastri 1946 English
          translation (the edition named in plan.md Section 4), OCR text layer
          from archive.org.
Maya   -- Book of Chilam Balam of Chumayel, Ralph L. Roys 1933. plan.md points
          at sacred-texts.com, which now returns 403 to everything non-browser;
          archive.org carries the same sacred-texts scan, public domain.
"""

import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0 (research; personal non-commercial corpus survey)"}

SOURCES = [
    (
        "roman/obsequens.html",
        "https://www.attalus.org/translate/obsequens.html",
    ),
    (
        "vedic/brihat_samhita_sastri_1946_djvu.txt",
        "https://archive.org/download/varahamihiras-brihat-samhita-by-v-subrahmanya-sastri/"
        "Varahamihira%27s%20Brihat%20Samhita%20by%20V%20Subrahmanya%20Sastri_djvu.txt",
    ),
    (
        "maya/chilam_balam_chumayel_djvu.txt",
        "https://archive.org/download/book-of-chilam-balam-the-of-chumayel/"
        "Book-of-Chilam-Balam-the-of-Chumayel_djvu.txt",
    ),
]


def main():
    for rel, url in SOURCES:
        out = RAW / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            print(f"skip {rel} ({out.stat().st_size:,} bytes)")
            continue
        print(f"get  {url}")
        req = urllib.request.Request(url, headers=UA)
        data = urllib.request.urlopen(req, timeout=180).read()
        out.write_bytes(data)
        print(f"     -> {rel} ({len(data):,} bytes)")


if __name__ == "__main__":
    main()
