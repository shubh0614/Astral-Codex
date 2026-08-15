"""
Score the vision extraction of TABLE 2 against the PDF's embedded text layer.

plan.md Section 4 sets a gate: test vision extraction on ONE table first, and
if it comes back with more than 30% field errors, abandon the full harvest and
fall back to a single narrow phenomenon. This measures that number instead of
guessing at it.

The text layer is used only as ground truth for scoring, not as the extraction
method -- the whole point of the vision approach is that the text layer loses
the column structure, which is exactly what makes it useless for extraction and
still fine for spot-checking individual values.
"""

import json
import re
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data" / "raw" / "korean" / "papers" / "meteor_records_analysis.pdf"
EXTRACT = ROOT / "data" / "raw" / "korean" / "vision_extract_table2.json"
PAGE = 21


def main():
    truth_text = pymupdf.open(PDF)[PAGE - 1].get_text()
    truth_nums = set(re.findall(r"\d+", truth_text))

    data = json.loads(EXTRACT.read_text(encoding="utf-8"))
    rows = data["rows"]

    checked = hits = 0
    misses = []
    for i, r in enumerate(rows):
        for field in ("jd", "day", "note"):
            v = r.get(field)
            if v is None:
                continue
            checked += 1
            if str(v) in truth_nums:
                hits += 1
            else:
                misses.append((i, field, v))
        # year out of the date string
        y = r["date_observation_YMD"].split()[0]
        checked += 1
        if y in truth_nums:
            hits += 1
        else:
            misses.append((i, "year", y))

    err = 1 - hits / checked
    print(f"rows extracted      : {len(rows)}")
    print(f"numeric fields check: {checked}")
    print(f"matched text layer  : {hits}")
    print(f"field error rate    : {err:.1%}   (plan.md gate: abandon if >30%)")
    if misses:
        print("\nmismatches:")
        for m in misses:
            print("   row", m[0], m[1], "=", m[2])

    # sanity: does the text layer preserve column structure at all?
    print("\n--- first 12 lines of the raw text layer, for comparison ---")
    for line in [l for l in truth_text.splitlines() if l.strip()][:12]:
        print("   |", line)


if __name__ == "__main__":
    main()
