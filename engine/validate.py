"""
Validate the calendar and sky layers against the diaries themselves.

The diaries record eclipses with a Babylonian month and day. A lunar eclipse can
only happen at full moon, a solar eclipse only at new moon. So converting those
dates and checking the computed lunar phase is an end-to-end test of the
calendar layer and the astronomy layer at once, with the tablets as ground
truth. If Nisannu 1 is off by a lunation, the phase will be nowhere near right.

usage: python engine/validate.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.bab_calendar import BabylonianCalendar, resolve_year
from engine.sky import Sky

ROOT = Path(__file__).resolve().parents[1]
UNITS = ROOT / "data" / "processed" / "babylonian_units.json"

LUNAR = re.compile(r"lunar eclipse|moon.{0,30}eclipsed|it was eclipsed", re.I)
SOLAR = re.compile(r"solar eclipse|sun.{0,20}eclipsed", re.I)


def collect(units, pattern, need_day=True):
    out = []
    for u in units:
        if not pattern.search(u["text"]):
            continue
        if not u.get("month") or (need_day and not u.get("day")):
            continue
        y, note = resolve_year(u.get("ancient_year"), u.get("date_bce"))
        if y is None:
            continue
        out.append((u, y, note))
    return out


def main():
    units = json.loads(UNITS.read_text(encoding="utf-8"))
    cal, sky = BabylonianCalendar(), Sky()

    print("=" * 76)
    print("Positions sanity check")
    print("=" * 76)
    jd = 1625456.5
    for b in ("sun", "moon", "venus", "mars", "jupiter", "saturn"):
        p = sky.position(b, jd)
        print(f"   {b:8s} RA {p['ra_hours']:7.3f}h  Dec {p['dec_deg']:+7.2f}  "
              f"lon {p['ecliptic_lon_deg']:6.2f}  {p['sign']}")
    print(f"   moon phase {sky.moon_phase_deg(jd):.2f} deg")

    for label, pattern, want_full in (("LUNAR", LUNAR, True), ("SOLAR", SOLAR, False)):
        rows = collect(units, pattern)
        print()
        print("=" * 76)
        print(f"{label} eclipse records: {len(rows)} with a resolvable date")
        print("=" * 76)
        if not rows:
            continue
        hits = 0
        for u, y, note in rows:
            conv = cal.to_jd(y, u["month"], u["day"],
                             intercalary="XII2" if "2" in (u["month"] or "") else None)
            if not conv:
                print(f"   {u['designation']:10s} m={u['month']:5s} d={u['day']:3s}  "
                      f"month not in year")
                continue
            phase = sky.moon_phase_deg(conv["jd"])
            beta = abs(sky.position("moon", conv["jd"],
                                    topocentric=False)["ecliptic_lat_deg"])
            ok = (phase > 170 and beta < 2.0) if want_full else (phase < 10 and beta < 2.0)
            hits += ok
            print(f"   {u['designation']:10s} {str(u['ancient_year']):10s} "
                  f"m={u['month']:5s} d={str(u['day']):3s} -> JD {conv['jd']:.1f}  "
                  f"phase {phase:6.1f}  beta {beta:5.2f}  {'OK' if ok else 'MISMATCH'}")
        print(f"\n   {hits}/{len(rows)} consistent with the recorded eclipse")

    # month-1 entries should be a thin crescent just after conjunction
    firsts = [u for u in units
              if u.get("day") == "1" and u.get("month")
              and "sunset to moonset" in u["text"].lower()]
    print()
    print("=" * 76)
    print(f"Month-first entries (expect a thin crescent, phase roughly 8 to 25 deg)")
    print("=" * 76)
    ok = 0
    for u in firsts[:20]:
        y, _ = resolve_year(u.get("ancient_year"), u.get("date_bce"))
        if y is None:
            continue
        conv = cal.to_jd(y, u["month"], 1)
        if not conv:
            continue
        ph = sky.moon_phase_deg(conv["jd"])
        good = 5 < ph < 30
        ok += good
        print(f"   {u['designation']:10s} m={u['month']:5s} -> phase {ph:6.2f} "
              f"{'OK' if good else 'off'}")
    print(f"\n   {ok}/{min(len(firsts),20)} look like a first crescent")


if __name__ == "__main__":
    main()
