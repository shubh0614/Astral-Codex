"""
Parse the Book of Chilam Balam of Chumayel (Roys 1933) into katun-keyed units.

The book is not uniform. It mixes prophecy, chronicle, ritual, creation myth,
colonial-era land records and 19th-century baptismal notes, plus OCR noise from
the plate captions. For Phase 0 we only care about material that is keyed to a
katun, so this pulls every paragraph that names one and records which section
of the book it came from -- prophecy and chronicle get counted separately,
because a chronicle entry ("9 Ahau.") is not a prophecy.

Output: data/processed/maya_katun_units.json
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "maya" / "chilam_balam_chumayel_djvu.txt"
OUT = ROOT / "data" / "processed" / "maya_katun_units.json"

SECTION_RE = re.compile(r"^\(([A-Z][^)]{6,80})\)\s*$", re.M)
KATUN_RE = re.compile(r"\bKatun\s+(\d{1,2}|Thirteen|Eleven|Nine|Seven|Five|Three|One)\s+Ahau\b", re.I)
BARE_AHAU_RE = re.compile(r"^\s*(\d{1,2})\s+Ahau\b")

WORDNUM = {"thirteen": 13, "eleven": 11, "nine": 9, "seven": 7, "five": 5, "three": 3, "one": 1}


def sections(text):
    marks = [(m.start(), m.group(1).strip()) for m in SECTION_RE.finditer(text)]
    for i, (off, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        yield name, off, text[off:end]


def clean(p):
    p = re.sub(r"\s+", " ", p).strip()
    return p


def is_noise(p):
    """Plate-caption OCR garbage: mostly non-words and stray punctuation."""
    letters = sum(c.isalpha() for c in p)
    if letters < 40:
        return True
    words = p.split()
    long_words = [w for w in words if len(w) > 3 and w.isalpha()]
    return len(long_words) / max(len(words), 1) < 0.35


def main():
    text = SRC.read_text(encoding="utf-8", errors="replace")
    out = []
    for name, off, body in sections(text):
        for para in re.split(r"\n\s*\n", body):
            p = clean(para)
            if not p or is_noise(p):
                continue
            kats = [
                int(k) if k.isdigit() else WORDNUM[k.lower()]
                for k in KATUN_RE.findall(p)
            ]
            bare = BARE_AHAU_RE.match(p)
            if not kats and not bare:
                continue
            out.append(
                {
                    "section": name,
                    "katuns": sorted(set(kats)),
                    "bare_chronicle_entry": bool(bare and not kats),
                    "text": p[:1500],
                    "n_chars": len(p),
                    "n_sentences": len([s for s in re.split(r"(?<=[.!?])\s+", p) if s.strip()]),
                }
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(out)} katun-keyed units -> {OUT}")

    import collections
    print("\nby section:")
    for k, v in collections.Counter(r["section"] for r in out).most_common():
        print(f"  {v:4d}  {k}")
    proph = [r for r in out if not r["bare_chronicle_entry"] and r["n_chars"] > 200]
    print(f"\nsubstantial non-chronicle units (>200 chars): {len(proph)}")
    allk = collections.Counter(k for r in out for k in r["katuns"])
    print(f"distinct katuns named: {sorted(allk)}")


if __name__ == "__main__":
    main()
