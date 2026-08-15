"""
Parse the Brihat Samhita (Sastri 1946) OCR text into individual sloka records.

The scan interleaves Devanagari and English. The Devanagari OCR layer is
unusable garbage, but the English translations are clean and consistently
marked: "Sloka 13.—The King who is in the height of glory..." or
"Slokas 15-16.—A horse with good features...".

Chapter (adhyaya) number comes from the running page headers, which look like
  Adh. XLIV. Sl. 15-16.]   or   [Adh. XVI. Sl. 35-37.
so we track the most recently seen one and attach it to following slokas.

Output: data/processed/vedic_slokas.json
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "vedic" / "brihat_samhita_sastri_1946_djvu.txt"
OUT = ROOT / "data" / "processed" / "vedic_slokas.json"

ADH_RE = re.compile(r"Adh\.?\s+([IVXLC]+)\.?\s*Sl", re.I)
# OCR renders the dash after "Sloka N" as any of - — .- ,- etc.
SLOKA_RE = re.compile(
    r"(?:Slokas?|Bloke|Sloke)\s*,?\s*(\d+)\s*(?:-|–|to)?\s*(\d+)?\s*[.,]?\s*[-—–]+\s*(.+?)(?=\n\s*\n|\Z)",
    re.S,
)

ROMAN = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8,
    "IX": 9, "X": 10, "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
}


def roman_to_int(s):
    s = s.upper()
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total, prev = 0, 0
    for ch in reversed(s):
        v = vals.get(ch, 0)
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    return total


def clean(s):
    s = re.sub(r"\[?Adh\.?\s+[IVXLC]+\.?\s*Sl[^\]\n]*\]?", " ", s, flags=re.I)
    s = re.sub(r"\n\s*\d{1,3}\s*\n", "\n", s)           # stray page numbers
    s = re.sub(r"[^\x00-\x7F]+", " ", s)                 # drop Devanagari OCR noise
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .,-—")


def main():
    text = SRC.read_text(encoding="utf-8", errors="replace")

    # index adhyaya markers by character offset
    marks = [(m.start(), roman_to_int(m.group(1))) for m in ADH_RE.finditer(text)]

    def adhyaya_at(pos):
        cur = None
        for off, num in marks:
            if off <= pos:
                cur = num
            else:
                break
        return cur

    out = []
    for m in SLOKA_RE.finditer(text):
        body = clean(m.group(3))
        if len(body) < 40:
            continue
        out.append(
            {
                "adhyaya": adhyaya_at(m.start()),
                "sloka_from": int(m.group(1)),
                "sloka_to": int(m.group(2)) if m.group(2) else int(m.group(1)),
                "text": body[:1200],
                "n_chars": len(body),
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(out)} slokas -> {OUT}")

    import collections
    c = collections.Counter(r["adhyaya"] for r in out)
    known = {k: v for k, v in c.items() if k}
    print(f"  adhyayas covered: {len(known)}  (min {min(known)}, max {max(known)})")
    print(f"  slokas with no adhyaya resolved: {c.get(None, 0)}")
    tgt = [3, 4, 5, 6, 7, 8, 9, 10, 11, 46]
    print(f"  plan.md target chapters 3-11 + 46: {sum(c.get(k,0) for k in tgt)} slokas")


if __name__ == "__main__":
    main()
