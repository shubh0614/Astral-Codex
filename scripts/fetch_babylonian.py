"""
Fetch the Babylonian Astronomical Diaries corpus (ADsD / ORACC).

Background on why this doesn't fetch from attalus.org:
attalus.org/docs/diaries.html is only an INDEX. Every translation link on it
points at repository.edition-topoi.org (Berlin Ancient Astronomy Project),
which is dead as of 2026-08 -- the host resolves (141.20.159.96) but refuses
connections on 80 and 443. ancient-astronomy.org no longer resolves at all.

So we use the other source named in plan.md Section 4: ORACC ADsD, which
publishes the Sachs & Hunger "Astronomical Diaries and Related Texts from
Babylonia" volumes as bulk JSON. CC BY-SA 3.0.

  ADART 1 -- Diaries 652-262 BC
  ADART 2 -- Diaries 261-165 BC
  ADART 3 -- Diaries 164-61 BC
  ADART 5 -- Lunar and planetary texts
  ADART 6 -- Goal year texts

Raw zips are stored unmodified under data/raw/babylonian/oracc_json/ per the
"store raw first" rule in CLAUDE.md. Nothing here cleans or filters.
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

    # keep the attalus index too, it's a useful cross-reference of which
    # diary years have published translations even though its links are dead
    idx = RAW / "_index_diaries.html"
    if not idx.exists():
        urllib.request.urlretrieve("https://www.attalus.org/docs/diaries.html", idx)
        print(f"     -> {idx.name}")


if __name__ == "__main__":
    main()
