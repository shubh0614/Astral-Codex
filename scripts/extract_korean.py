"""
Build the Korean Phase 0 candidate set from the two harvested papers.

Two different shapes of source, which is the finding plan.md did not anticipate:

  prose      Lee et al. 2014 keeps its Halley records as running text in the
             appendices, "September 3: A comet appeared in the Samtae
             constellation..." Ordinary parsing, no vision needed, and it
             carries a target TEXT as well as the facts.
  tabular    the meteor paper publishes records as a table: date, Julian Day,
             shower name, source sigla. Vision extraction handles it (0% field
             error, notes/korean_vision_test.md) but a table row has no prose,
             so it supplies conditioning facts with nothing to generate.

Output: data/processed/korean_candidates.json
"""

import json
import re
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "data" / "raw" / "korean" / "papers"
VISION = ROOT / "data" / "raw" / "korean" / "vision_extract_table2.json"
OUT = ROOT / "data" / "processed" / "korean_candidates.json"

MONTHS = ("January|February|March|April|May|June|July|August|September|"
          "October|November|December")
REC = re.compile(rf"({MONTHS})\s+(\d{{1,2}}):\s*(.+?)(?=(?:{MONTHS})\s+\d{{1,2}}:|$)",
                 re.S)
SIGLA = {"GS": "Goryeosa", "GJ": "Goryeosa Jeoryo", "BG": "Jeungbomunheonbigo",
         "DT": "Dongguk Tonggam"}


def prose_records():
    doc = pymupdf.open(PAPERS / "halley_korean_records.pdf")
    full = "\n".join(p.get_text() for p in doc)
    out = []
    for m in re.finditer(r"A\.(\d)\s+Halley.s comet in (\d{4})(.*?)(?=A\.\d\s+Halley|ACKNOWLEDG)",
                         full, re.S):
        year = m.group(2)
        for r in REC.finditer(m.group(3)):
            text = re.sub(r"\s+", " ", r.group(3)).strip()
            src = re.findall(r"\b(GS|GJ|BG|DT)\b", text)
            out.append({
                "kind": "prose",
                "apparition_year": int(year),
                "date": f"{r.group(1)} {r.group(2)}, {year}",
                "text": text,
                "sources": sorted({SIGLA[s] for s in src}),
                "paper": "Lee et al. 2014, Korean Historical Records on Halley's Comet",
            })
    return out


def table_records():
    data = json.loads(VISION.read_text(encoding="utf-8"))
    out = []
    for r in data["rows"]:
        out.append({
            "kind": "table",
            "date": r["date_observation_YMD"],
            "jd": r.get("jd"),
            "shower": r.get("shower"),
            "estimated_date": r.get("estimated_date"),
            "period": r.get("period"),
            "sources": r.get("ref"),
            "note_code": r.get("note"),
            "text": None,
            "paper": "Analysis of historical meteor and meteor shower records, TABLE 2",
        })
    return out


def main():
    recs = prose_records() + table_records()
    OUT.write_text(json.dumps(recs, indent=2, ensure_ascii=False), encoding="utf-8")
    import collections
    c = collections.Counter(r["kind"] for r in recs)
    print(f"candidates: {len(recs)}   {dict(c)}")
    print("\nprose records:")
    for r in recs:
        if r["kind"] == "prose":
            print(f"   {r['date']:22s} {r['text'][:95]}")
    print(f"\ntable records: {c['table']} rows, none of which carry any prose")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
