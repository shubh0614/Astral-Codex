"""
Split the scraped tablets into dated observation units and score each against
the clean-triple gate in plan.md Section 4. Writes
data/processed/babylonian_units.json.

The unit is one dated night, not one tablet, per plan.md Section 2. Why the
">2 sentences" criterion was replaced is in notes/phase0_results.md.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "babylonian" / "translations.jsonl"
OUT = ROOT / "data" / "processed" / "babylonian_units.json"

DAY_RE = re.compile(
    r"(?=(?:Night of the|That night,|The)\s+\d{1,2}(?:st|nd|rd|th)\b)|(?=\bMonth\s+[IVX]+)",
)
MONTH_RE = re.compile(r"\bMonth\s+([IVX]+₂?|[IVX]+2?)\b")
DAY_NUM_RE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)\b")

PLANETS = r"(?:moon|sun|Venus|Mars|Mercury|Jupiter|Saturn|Sirius)"
STAR_RE = re.compile(r"[α-ω]\s*[A-Z][a-z]+")
ZODIAC = (
    r"(?:Pisces|Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpi\w+|"
    r"Sagittarius|Capricorn\w*|Aquarius|Auriga|Pleiades)"
)
EVENTS = (
    r"(?:eclipse\w*|first appearance|last appearance|became stationary|"
    r"acronychal rising|opposition|conjunction|solstice|equinox|"
    r"sunset to moonset|moonset to sunrise|sunrise to sunset|rose|set\b)"
)
ASTRO_RE = re.compile(f"{PLANETS}|{ZODIAC}|{EVENTS}", re.I)
RELATION_RE = re.compile(
    r"\b(?:above|below|in front of|behind|to the east|to the west|"
    r"north|south|passed|cubit|finger|degrees?|°)\b",
    re.I,
)

WEATHER_RE = re.compile(
    r"\b(?:cloud\w*|overcast|rain|thunder|lightning|fog|dew|mist|wind|hail|"
    r"sandal|storm)\b",
    re.I,
)
NON_ASTRO_RE = re.compile(
    r"\b(?:river level|equivalent|shekel|barley|dates|cress|sesame|wool|"
    r"purchased|market)\b",
    re.I,
)

ELLIPSIS_RE = re.compile(r"\[\s*\.\.\.\s*\]|\.\.\.")


def n_sentences(t):
    return len([s for s in re.split(r"(?<=[.!?])\s+", t) if len(s.strip()) > 3])


INTACT_OBS_RE = re.compile(
    r"(?:%s)[^.;\[\]]{0,60}?"                       # a body, then a short span
    r"(?:\d|\bnn\b)[^.;\[\]]{0,40}?"                # a measurement
    r"(?:cubit|finger|°|º)[^.;\[\]]{0,40}?"         # its unit
    r"(?:above|below|in front of|behind|to the east|to the west|"
    r"north|south|passed)" % PLANETS,
    re.I,
)
LUNAR_SIX_RE = re.compile(
    r"(?:sunset to moonset|moonset to sunrise|moonrise to sunset|"
    r"sunrise to moonset|sunset to moonrise|moonrise to sunrise)\s*:?\s*"
    r"\[?\s*(?:x\]?\+)?\d",
    re.I,
)
EVENT_OBS_RE = re.compile(
    r"(?:first appearance|last appearance|became stationary|acronychal rising|"
    r"eclipse|equinox|solstice|reached\s+(?:%s))" % ZODIAC,
    re.I,
)
PLANET_IN_SIGN_RE = re.compile(r"(?:%s)\s+was\s+in\s+(?:%s)" % (PLANETS, ZODIAC), re.I)

NARRATIVE_RE = re.compile(
    r"\b(?:satrap|king|troops|entered Babylon|general|sacrifice[sd]?|"
    r"went from|encamped)\b", re.I
)


def classify(unit, month_resolved, month_inferable, has_year):
    """Return (verdict, reasons, stats) against the clean-triple gate."""
    t = unit["text"]
    reasons = []
    has_day = bool(unit["day"])

    gaps = len(ELLIPSIS_RE.findall(t))
    runs = [s.strip() for s in ELLIPSIS_RE.split(t) if s.strip()]
    longest_run = max((len(s) for s in runs), default=0)

    intact = bool(
        INTACT_OBS_RE.search(t)
        or LUNAR_SIX_RE.search(t)
        or EVENT_OBS_RE.search(t)
        or PLANET_IN_SIGN_RE.search(t)
    )
    damaged = bool(ASTRO_RE.search(t) or STAR_RE.search(t))

    date_ok = has_year and month_resolved
    if not date_ok:
        reasons.append(
            "month not resolved in text (inferable from tablet)"
            if month_inferable else "no recoverable year+month"
        )
    if not intact:
        if damaged:
            reasons.append("astronomical content present but broken by a gap")
        elif NARRATIVE_RE.search(t):
            reasons.append("historical/narrative note")
        elif WEATHER_RE.search(t) or NON_ASTRO_RE.search(t):
            reasons.append("weather/market/river note only")
        else:
            reasons.append("no astronomical content")
    if longest_run < 60:
        reasons.append(f"longest continuous run only {longest_run} chars")

    heavy = gaps >= 3
    enough_text = longest_run >= 60

    if date_ok and intact and enough_text:
        verdict = "usable"
    elif intact or (date_ok and damaged):
        verdict = "ambiguous"
    else:
        verdict = "reject"

    return verdict, reasons, {
        "gaps": gaps, "sentences": n_sentences(t), "heavy": heavy,
        "longest_run": longest_run, "intact_observation": intact,
        "has_day": has_day, "month_resolved": month_resolved,
    }


def main():
    recs = [json.loads(l) for l in SRC.read_text(encoding="utf-8").splitlines()]
    units = []

    for r in recs:
        has_year = bool(r.get("ancient_year") or r.get("date_bce"))
        stream = " ".join(l["text"] for l in r["lines"])
        stream = re.sub(r"\s+", " ", stream)

        pieces = [p.strip() for p in DAY_RE.split(stream) if p and p.strip()]
        cur_month = None
        cat_month = bool((r.get("months_recorded") or "").strip(" []"))

        for p in pieces:
            m = MONTH_RE.search(p)
            if m:
                cur_month = m.group(1)
            d = DAY_NUM_RE.search(p[:40])
            unit = {
                "text_id": r["text_id"],
                "volume": r["volume"],
                "designation": r["designation"],
                "date_bce": r.get("date_bce"),
                "ancient_year": r.get("ancient_year"),
                "month": cur_month,
                "day": d.group(1) if d else None,
                "text": p[:900],
                "n_chars": len(p),
            }
            verdict, reasons, stats = classify(
                unit, bool(cur_month), bool(cat_month), has_year
            )
            unit.update(verdict=verdict, reasons=reasons, **stats)
            units.append(unit)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(units, indent=2, ensure_ascii=False), encoding="utf-8")

    import collections
    c = collections.Counter(u["verdict"] for u in units)
    n = len(units)
    print(f"tablets: {len(recs)}   observation units: {n}")
    for k in ("usable", "ambiguous", "reject"):
        print(f"  {k:10s} {c[k]:6d}  {c[k]/n:6.1%}")
    frag = sum(1 for u in units if u["heavy"])
    print(f"\nheavily fragmentary (>=3 gaps): {frag}  ({frag/n:.1%})")
    print(f"units with zero [...] gaps    : {sum(1 for u in units if u['gaps']==0)}")
    us = [u for u in units if u["verdict"] == "usable"]
    print(f"\nof the {len(us)} usable units:")
    print(f"  with zero gaps        : {sum(1 for u in us if u['gaps']==0)}")
    print(f"  heavily fragmentary   : {sum(1 for u in us if u['heavy'])}")
    amb = [u for u in units if u["verdict"] == "ambiguous"]
    monthless = sum(1 for u in amb if not u["month_resolved"] and u["intact_observation"])
    print(f"\nambiguous only because the month was not resolved in text: {monthless}")
    print(f"  (these carry an intact observation and are recoverable with a better parse)")
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
