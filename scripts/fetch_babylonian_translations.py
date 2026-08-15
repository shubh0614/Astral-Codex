"""
Scrape English translations of the Astronomical Diaries from ORACC ADsD.

Why scrape HTML instead of using the JSON dump: the open-data zips
(scripts/fetch_babylonian.py) contain the Akkadian transliteration and the
lemmatisation, but NOT the English translation text. index-tra.json references
translation files named like `X102613_project-en` that are simply absent from
the zip. The English only exists in the rendered pages, inside <td class="t1 xtr">
cells, one cell per tablet line.

Output: data/raw/babylonian/oracc_html/<TEXTID>.html  (unmodified page)
        data/raw/babylonian/translations.jsonl        (one record per tablet)

Nothing here filters or judges quality -- that's the annotation step.
"""

import json
import re
import html
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "babylonian"
HTML_DIR = RAW / "oracc_html"
ZIPS = RAW / "oracc_json"

# diary volumes only -- adart5 (lunar/planetary) and adart6 (goal-year) are a
# different genre of text and are held back for now
VOLUMES = ["adart1", "adart2", "adart3"]
UA = {"User-Agent": "Mozilla/5.0 (research; personal non-commercial corpus survey)"}

LINE_RE = re.compile(r'<td[^>]*class="[^"]*xtr[^"]*"[^>]*>(.*?)</td>', re.S)
LABEL_RE = re.compile(r"^\(([^)]*)\)\s*")


def text_ids(vol):
    """Text ids that actually have a corpusjson entry, in catalogue order."""
    z = zipfile.ZipFile(ZIPS / f"adsd-{vol}.zip")
    ids = sorted(
        Path(n).stem
        for n in z.namelist()
        if "/corpusjson/" in n and n.endswith(".json")
    )
    cat = json.loads(z.read(f"adsd/{vol}/catalogue.json"))["members"]
    return [(i, cat.get(i, {})) for i in ids]


def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).replace("\xa0", " ").strip()


def scrape(vol, tid):
    url = f"http://oracc.museum.upenn.edu/adsd/{vol}/{tid}/html"
    out = HTML_DIR / f"{tid}.html"
    if out.exists():
        page = out.read_text(encoding="utf-8", errors="replace")
    else:
        req = urllib.request.Request(url, headers=UA)
        page = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
        out.write_text(page, encoding="utf-8")
        time.sleep(0.7)  # be polite to a university server

    lines = []
    for cell in LINE_RE.findall(page):
        s = strip_tags(cell)
        if not s:
            continue
        m = LABEL_RE.match(s)
        label = m.group(1) if m else ""
        body = s[m.end():] if m else s
        lines.append({"label": label, "text": body})
    return url, lines


def main():
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    out = RAW / "translations.jsonl"
    n = 0
    with out.open("w", encoding="utf-8") as fh:
        for vol in VOLUMES:
            for tid, meta in text_ids(vol):
                try:
                    url, lines = scrape(vol, tid)
                except Exception as e:
                    print(f"  !! {vol}/{tid}: {e}")
                    continue
                if not lines:
                    continue
                rec = {
                    "text_id": tid,
                    "volume": vol,
                    "url": url,
                    "designation": meta.get("designation"),
                    "date_bce": meta.get("date_bce"),
                    "ancient_year": meta.get("ancient_year"),
                    "months_recorded": meta.get("months_recorded"),
                    "provenience": meta.get("provenience"),
                    "museum_no": meta.get("museum_no"),
                    "lines": lines,
                }
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
                if n % 25 == 0:
                    print(f"  {n} tablets")
    print(f"wrote {n} tablets -> {out}")


if __name__ == "__main__":
    main()
