"""
Extract an OBSERVATION_STATE from the diary text of each usable unit.

States are derived from the TEXT, not from the engine. The engine's date
conversion is right about 65% of the time, so computing states from dates would
attach a wrong sky state to roughly a third of the training pairs and teach the
model to ignore the state entirely. The engine cross-checks these, it does not
produce them.

Weather is captured too. The diaries record it and the target text contains it,
so leaving it out of the state would train the model to invent it.

Output: data/processed/babylonian_states.json
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "processed" / "babylonian_units.json"
OUT = ROOT / "data" / "processed" / "babylonian_states.json"

BODY = r"moon|sun|Venus|Mars|Mercury|Jupiter|Saturn|Sirius"
STAR = r"[α-ω]\s*[A-Z][a-z]+(?:orum|ini|ae|is|i|um)?"
TARGET = rf"(?:{STAR}|{BODY})"
MEAS = (r"(?:[\d½⅓⅔¼]+(?:\s*\d/\d)?(?:\s*\d+)?"
        r"\s*(?:cubits?|fingers?)(?:\s+\d+\s*fingers?)?)")
REL = r"above|below|in front of|behind"

WATCH = re.compile(
    r"(beginning of the night|first part of the night|middle part of the night|"
    r"last part of the night|in the morning|in the afternoon|at noon)", re.I)

CONJ = re.compile(
    rf"(?P<body>{BODY})\s+(?:was|stood)\s+(?P<meas>{MEAS})?\s*"
    rf"(?P<rel>{REL})\s+(?P<target>{TARGET})", re.I)
STOOD = re.compile(
    rf"it stood\s+(?P<meas>{MEAS})\s+(?P<rel>{REL})\s+(?P<target>{TARGET})"
    rf"(?:\s+to the (?P<dir>east|west))?", re.I)
LATITUDE = re.compile(
    rf"(?P<body>{BODY})\s+being\s+(?P<meas>{MEAS})\s+"
    r"(?P<dir>high to the north|low to the south|back to the west|"
    r"back to the east)", re.I)
PASSED = re.compile(
    rf"(?P<body>{BODY})\s+having passed\s+(?P<meas>{MEAS})?\s*to the "
    r"(?P<dir>east|west)", re.I)
LUNAR6 = re.compile(
    r"(?P<kind>sunset to moonset|moonset to sunrise|moonrise to sunset|"
    r"sunrise to moonset|sunset to moonrise|moonrise to sunrise)\s*:?\s*"
    r"(?P<val>\d+(?:\s*°)?(?:\s*\d+')?)", re.I)
APPEAR = re.compile(
    rf"(?P<body>{BODY})[’']?s?\s+(?P<kind>first|last)\s+appearance"
    r"(?:\s+in the (?P<dir>east|west))?"
    r"(?:\s+in (?:the (?:beginning|middle|end) of )?(?P<sign>[A-Z][a-z]+))?", re.I)
STATION = re.compile(
    rf"(?P<body>{BODY})\s+became stationary(?:\s+to the (?P<dir>east|west))?", re.I)
ACRO = re.compile(rf"(?P<body>{BODY})[’']?s?\s+acronychal rising", re.I)
WEATHER = re.compile(
    r"(clouds? (?:were|crossed)[^;.]*|very overcast|overcast|"
    r"a little rain shower|rain shower|rain DUL|thunder|lightning flashed|"
    r"the (?:north|south|east|west) wind blew|gusty [a-z]+ wind|mist|fog|"
    r"earthshine|it was bright|it was faint)", re.I)

ZODIAC = (r"Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpius|Scorpio|"
          r"Sagittarius|Capricorn|Aquarius|Pisces")
# Signs count as hard facts too: an entry saying "in the end of Libra" against a
# state that never mentions Libra teaches the model to invent a location.
BODY_MENTION = re.compile(rf"\b(?:{BODY})\b|{STAR}|\b(?:{ZODIAC})\b", re.I)
SIGN_IN_TEXT = re.compile(rf"\b(?:{ZODIAC})\b", re.I)
DAMAGE = re.compile(r"[\[\]⸢⸣]")
OFF_TOPIC = re.compile(
    r"\b(equivalent|shekel|barley|dates|cress|sesame|wool|purchased|"
    r"satrap|troops|entered Babylon|sacrifice)\b", re.I)
PLANET_WORDS = {"venus", "mars", "mercury", "jupiter", "saturn", "sirius",
                "moon", "sun"}


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip(" ,.;"))


def extract(text):
    ev, seen = [], set()
    for m in CONJ.finditer(text):
        key = (norm(m.group("body")).lower(), norm(m.group("target")).lower())
        if key in seen:
            continue
        seen.add(key)
        ev.append({"event": "conjunction",
                   "objects": [norm(m.group("body")), norm(m.group("target"))],
                   "relation": norm(m.group("rel")),
                   "separation": norm(m.group("meas"))})
    for m in STOOD.finditer(text):
        key = ("moon", norm(m.group("target")).lower())
        if key in seen:
            continue
        seen.add(key)
        ev.append({"event": "conjunction",
                   "objects": ["moon", norm(m.group("target"))],
                   "relation": norm(m.group("rel")),
                   "separation": norm(m.group("meas")),
                   "direction": norm(m.group("dir"))})
    for m in LATITUDE.finditer(text):
        ev.append({"event": "latitude", "objects": [norm(m.group("body"))],
                   "offset": norm(m.group("meas")),
                   "direction": norm(m.group("dir"))})
    for m in PASSED.finditer(text):
        ev.append({"event": "motion", "objects": [norm(m.group("body"))],
                   "passed": norm(m.group("meas")),
                   "direction": norm(m.group("dir"))})
    for m in LUNAR6.finditer(text):
        ev.append({"event": "lunar_six", "interval": norm(m.group("kind")),
                   "value": norm(m.group("val"))})
    for m in APPEAR.finditer(text):
        e = {"event": f"{m.group('kind').lower()}_appearance",
             "objects": [norm(m.group("body"))]}
        if m.group("dir"):
            e["direction"] = norm(m.group("dir"))
        if m.group("sign"):
            e["sign"] = norm(m.group("sign"))
        ev.append(e)
    for m in STATION.finditer(text):
        e = {"event": "stationary_point", "objects": [norm(m.group("body"))]}
        if m.group("dir"):
            e["station_direction"] = norm(m.group("dir"))
        # the sign usually follows: "it became stationary in the end of Libra"
        tail = text[m.end():m.end() + 60]
        s = SIGN_IN_TEXT.search(tail)
        if s:
            e["sign"] = norm(s.group(0))
        ev.append(e)
    for m in ACRO.finditer(text):
        ev.append({"event": "acronychal_rising",
                   "objects": [norm(m.group("body"))]})
    if re.search(r"eclipse|eclipsed", text, re.I):
        ev.append({"event": "eclipse", "objects": ["moon"]})

    conditions = sorted({norm(w) for w in WEATHER.findall(text)})
    return ev, conditions


def bodies_in(events):
    out = []
    for e in events:
        for o in e.get("objects", []):
            if o not in out:
                out.append(o)
    return out


def bodies_mentioned(text):
    """Every celestial object named in the entry. Bracket markers are stripped
    first, otherwise a name split by tablet damage such as '[Mer]cury' slips
    past the check and the pair silently teaches hallucination."""
    text = DAMAGE.sub("", text)
    out = set()
    for m in BODY_MENTION.finditer(text):
        s = norm(m.group(0))
        out.add(s.lower() if s.split()[0].lower() in PLANET_WORDS else s.lower())
    return out


def consistency(entry, events):
    """Every object and sign in the ENTRY must appear in the STATE. This is
    criterion (b) of the baseline scorer, applied at build time rather than at
    eval time."""
    in_state = {b.lower() for b in bodies_in(events)}
    for e in events:
        if e.get("sign"):
            in_state.add(e["sign"].lower())
    return sorted(b for b in bodies_mentioned(entry)
                  if not any(b in s or s in b for s in in_state))


def render_state(unit, events, conditions, entry):
    lines = ["<TRADITION=BABYLONIAN>", "<GENRE=OBSERVATION>", "<OBSERVATION_STATE>"]
    d = []
    if unit.get("ancient_year"):
        d.append(f"year {unit['ancient_year']}")
    if unit.get("month"):
        d.append(f"month {unit['month']}")
    if unit.get("day"):
        d.append(f"day {unit['day']}")
    lines.append("  Date: " + ", ".join(d))
    w = WATCH.search(entry)
    if w:
        lines.append(f"  Watch: {w.group(1).lower()}")
    for b in bodies_in(events):
        lines.append(f"  {b}: observed")
    if conditions:
        lines.append("  Conditions: " + "; ".join(conditions))
    lines.append("  Events: " + json.dumps(events, ensure_ascii=False))
    lines.append("</OBSERVATION_STATE>")
    lines.append("<ENTRY>")
    return "\n".join(lines)


def main():
    units = json.loads(SRC.read_text(encoding="utf-8"))
    out = []
    dropped = {"no_events": 0, "off_topic": 0, "inconsistent": 0}
    for u in units:
        if u["verdict"] != "usable":
            continue
        # Strip tablet-damage brackets before doing anything else. They break
        # the extraction regexes mid-phrase ('[Mercury's last appearance [in
        # the west in] Cancer' loses its direction and sign), and leaving them
        # in the target teaches the model to emit brackets as a stylistic tic,
        # which plan.md Section 4 warns about explicitly.
        entry = norm(DAMAGE.sub("", u["text"]))
        events, conditions = extract(entry)
        if not events:
            dropped["no_events"] += 1
            continue
        if OFF_TOPIC.search(entry):
            dropped["off_topic"] += 1
            continue
        if consistency(entry, events):
            dropped["inconsistent"] += 1
            continue
        out.append({
            "text_id": u["text_id"], "volume": u["volume"],
            "designation": u["designation"], "ancient_year": u.get("ancient_year"),
            "month": u.get("month"), "day": u.get("day"), "gaps": u["gaps"],
            "date_confidence": u.get("date_confidence"),
            "year_source": u.get("year_source"),
            "events": events, "conditions": conditions, "n_events": len(events),
            "state": render_state(u, events, conditions, entry), "entry": entry,
        })
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    import collections
    usable = sum(1 for u in units if u["verdict"] == "usable")
    print(f"usable units                    : {usable}")
    print(f"  dropped, no events parsed     : {dropped['no_events']}")
    print(f"  dropped, market/narrative text: {dropped['off_topic']}")
    print(f"  dropped, entry names an object the state does not: "
          f"{dropped['inconsistent']}")
    print(f"states kept                     : {len(out)}")
    print(f"  of which zero-gap             : {sum(1 for r in out if r['gaps']==0)}")
    ec = collections.Counter(e["event"] for r in out for e in r["events"])
    print("\nevent types:")
    for k, v in ec.most_common():
        print(f"   {k:20s} {v:6d}")
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
