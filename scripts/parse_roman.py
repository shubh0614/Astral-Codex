"""
Parse Julius Obsequens into one record per prodigy-year entry.
Writes data/processed/roman_entries.json. Structure extraction only.
"""

import json
import re
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "roman" / "obsequens.html"
OUT = ROOT / "data" / "processed" / "roman_entries.json"

ENTRY_RE = re.compile(
    r'<A CLASS="ref" NAME="(\d+[A-Za-z]?)">\[[^\]]*\]</A>(.*?)(?=<A CLASS="ref" NAME="|\Z)',
    re.S | re.I,
)
CONSUL_RE = re.compile(r"Consuls?:\s*(?:&nbsp;)*\s*<B>(.*?)</B>", re.S | re.I)
YEAR_RE = re.compile(r"\{\s*<I>\s*([^<]*?)\s*</I>\s*\}", re.S | re.I)


def strip_tags(s):
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</p>|<p>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    return re.sub(r"\n{2,}", "\n", s).strip()


def main():
    doc = SRC.read_text(encoding="utf-8", errors="replace")
    out = []
    for num, body in ENTRY_RE.findall(doc):
        cm, ym = CONSUL_RE.search(body), YEAR_RE.search(body)
        prose = body[ym.end():] if ym else body
        prose = strip_tags(prose)
        if not prose:
            continue
        out.append(
            {
                "entry": num,
                "consuls": strip_tags(cm.group(1)) if cm else None,
                "year": strip_tags(ym.group(1)) if ym else None,
                "text": prose,
                "n_sentences": len([s for s in re.split(r"(?<=[.!?])\s+", prose) if s.strip()]),
                "n_chars": len(prose),
            }
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(out)} entries -> {OUT}")
    yrs = [e for e in out if e["year"]]
    print(f"  with a year: {len(yrs)}   with consuls: {sum(1 for e in out if e['consuls'])}")
    print(f"  median chars: {sorted(e['n_chars'] for e in out)[len(out)//2]}")


if __name__ == "__main__":
    main()
