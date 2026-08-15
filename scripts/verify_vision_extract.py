"""
Score the vision extraction of TABLE 2 against the PDF text layer, for the
Korean gate in plan.md Section 4. Result is in notes/korean_vision_test.md.
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

    print("\n--- first 12 lines of the raw text layer, for comparison ---")
    for line in [l for l in truth_text.splitlines() if l.strip()][:12]:
        print("   |", line)


if __name__ == "__main__":
    main()
