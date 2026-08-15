"""
Download the ORACC ADsD bulk JSON (Sachs & Hunger diary volumes) to
data/raw/babylonian/oracc_json/. Stores raw, cleans nothing.

The attalus.org route named in plan.md is dead; see notes/SOURCES.md.
"""

import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "babylonian"
DEST = RAW / "oracc_json"

CORPORA = ["adart1", "adart2", "adart3", "adart5", "adart6"]
BASE = "http://oracc.museum.upenn.edu/json/adsd-{}.zip"


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for name in CORPORA:
        url = BASE.format(name)
        out = DEST / f"adsd-{name}.zip"
        if out.exists():
            print(f"skip {out.name} ({out.stat().st_size:,} bytes, already here)")
            continue
        print(f"get  {url}")
        urllib.request.urlretrieve(url, out)
        print(f"     -> {out.name} ({out.stat().st_size:,} bytes)")

    idx = RAW / "_index_diaries.html"
    if not idx.exists():
        urllib.request.urlretrieve("https://www.attalus.org/docs/diaries.html", idx)
        print(f"     -> {idx.name}")


if __name__ == "__main__":
    main()
