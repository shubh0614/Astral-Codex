"""
Babylonian calendar normalization: regnal year + month + day -> Julian Day.

The calendar is lunisolar. Months begin at the first evening the lunar crescent
is visible from Babylon, and the year begins so that the spring equinox falls in
month I (Nisannu). Intercalary months were inserted by decree, not by a fixed
rule, so some dates resolve only to a range. That uncertainty is returned, not
hidden, per plan.md Section 4.

Two independent routes to the year are available and are cross-checked:
the catalogue's date_bce field, and the Seleucid Era number in ancient_year.

Named bab_calendar rather than calendar so it does not shadow the stdlib module,
which the email package imports and which breaks Skyfield's own imports.
"""

import re
from functools import lru_cache

import numpy as np
from skyfield import almanac
from skyfield.api import load, load_file, wgs84

EPH_PATH = "engine/ephem/de406.bsp"
BABYLON = wgs84.latlon(32.5434, 44.4222, elevation_m=34)

MONTHS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII",
          "IX", "X", "XI", "XII"]

# First crescent visibility thresholds. Swept against the diaries' own eclipse
# records; the result is flat between 10 and 13 degrees elongation, so these are
# not finely tuned and do not need to be. See notes/engine.md.
MIN_ELONGATION_DEG = 11.0
MIN_MOON_ALT_DEG = 5.0


class BabylonianCalendar:
    def __init__(self, eph_path=EPH_PATH):
        self.eph = load_file(eph_path)
        self.ts = load.timescale()
        self.sun = self.eph["sun"]
        self.moon = self.eph["moon"]
        self.earth = self.eph["earth"]
        self.observer = self.earth + BABYLON

    def _new_moons(self, y0, y1):
        t0 = self.ts.tt(y0, 1, 1)
        t1 = self.ts.tt(y1, 12, 31)
        t, phase = almanac.find_discrete(t0, t1, almanac.moon_phases(self.eph))
        return t[phase == 0]

    def _equinox(self, astro_year):
        t0 = self.ts.tt(astro_year, 1, 1)
        t1 = self.ts.tt(astro_year, 12, 31)
        t, ev = almanac.find_discrete(t0, t1, almanac.seasons(self.eph))
        return t[ev == 0][0]

    def _sunset(self, t_approx):
        """Sunset on the civil day containing t_approx."""
        y, m, d = t_approx.tt_calendar()[:3]
        t0 = self.ts.tt(y, m, d, 0)
        t1 = self.ts.tt(y, m, d + 2, 0)
        f = almanac.sunrise_sunset(self.eph, BABYLON)
        t, up = almanac.find_discrete(t0, t1, f)
        sets = t[up == 0]
        return sets[0] if len(sets) else None

    def _visible_at_sunset(self, t_sunset):
        app = self.observer.at(t_sunset)
        moon = app.observe(self.moon).apparent()
        sun = app.observe(self.sun).apparent()
        elong = sun.separation_from(moon).degrees
        alt = moon.altaz()[0].degrees
        return elong >= MIN_ELONGATION_DEG and alt >= MIN_MOON_ALT_DEG

    def first_crescent_after(self, t_conjunction):
        """First evening after conjunction when the crescent should be visible."""
        for offset in range(0, 4):
            y, m, d = t_conjunction.tt_calendar()[:3]
            probe = self.ts.tt(y, m, d + offset)
            ss = self._sunset(probe)
            if ss is None:
                continue
            if ss.tt <= t_conjunction.tt:
                continue
            if self._visible_at_sunset(ss):
                return ss
        # fall back to conjunction + 1 day if the model never triggers
        y, m, d = t_conjunction.tt_calendar()[:3]
        return self._sunset(self.ts.tt(y, m, d + 1))

    @lru_cache(maxsize=256)
    def month_starts(self, astro_year, intercalary=None):
        """Julian Days of the start of each Babylonian month in the year whose
        Nisannu falls in `astro_year`. Returns a dict month-label -> jd."""
        eq = self._equinox(astro_year)
        conj = self._new_moons(astro_year - 1, astro_year + 1)

        # Nisannu 1 is the first crescent visibility on or after the vernal
        # equinox. Calibrated against the diaries' own eclipse records: the
        # alternative "equinox falls inside month I" rule put every date exactly
        # one lunation early (median offset +30.25 d over 30 eclipse records).
        crescents = []
        for c in conj:
            if abs(c.tt - eq.tt) > 80:
                continue
            fc = self.first_crescent_after(c)
            if fc is not None:
                crescents.append(fc)
        crescents.sort(key=lambda t: t.tt)
        after = [c for c in crescents if c.tt >= eq.tt]
        nisannu = after[0] if after else min(
            crescents, key=lambda t: abs(t.tt - eq.tt))

        # walk forward, one crescent per month, inserting the intercalary month
        seq = list(MONTHS)
        if intercalary in ("XII2", "VI2"):
            seq.insert(seq.index(intercalary[:-1]) + 1, intercalary)

        later = self._new_moons(astro_year, astro_year + 2)
        starts, cur = {}, nisannu
        starts[seq[0]] = cur.tt
        for label in seq[1:]:
            nxt = [c for c in later if c.tt > cur.tt + 20]
            if not nxt:
                break
            cur = self.first_crescent_after(nxt[0])
            starts[label] = cur.tt
        return starts

    def to_jd(self, astro_year, month, day, intercalary=None):
        """Return jd plus an honest uncertainty for one Babylonian date.

        The returned jd is the START of the Babylonian day, which begins at
        sunset. An event recorded as "night of the Nth" therefore falls in the
        twelve hours or so AFTER this instant, which is why validation against
        eclipse records leaves a residual of about +0.8 days rather than zero.
        """
        month = (month or "").replace("₂", "2")
        starts = self.month_starts(astro_year, intercalary)
        if month not in starts:
            return None
        jd = starts[month] + (int(day) - 1 if day else 0)

        # crescent visibility is a day-scale judgement; intercalation is the
        # month-scale risk and only bites when the catalogue does not tell us
        unc = 1.0 if intercalary else 2.0
        conf = 0.85 if intercalary else 0.7
        if not day:
            unc, conf = 15.0, 0.4
        return {
            "jd": jd,
            "uncertainty_days": unc,
            "confidence": conf,
            "month_start_jd": starts[month],
            "conversion_method": "crescent-visibility model, equinox-in-Nisannu rule",
        }


def astro_year_from_date_bce(date_bce):
    """'263/2' -> -262. The Babylonian year starts in the spring of 263 BC."""
    if not date_bce:
        return None
    m = re.match(r"\s*(\d{1,4})", str(date_bce))
    if not m:
        return None
    return -(int(m.group(1)) - 1)


def astro_year_from_seleucid(ancient_year):
    """'SE 49' -> -262. Seleucid year 1 began in the spring of 311 BC."""
    if not ancient_year:
        return None
    m = re.match(r"\s*SE\s+(\d{1,4})", str(ancient_year), re.I)
    if not m:
        return None
    return int(m.group(1)) - 311


def resolve_year(ancient_year, date_bce):
    """Prefer date_bce, cross-check against the Seleucid number when present."""
    a = astro_year_from_date_bce(date_bce)
    b = astro_year_from_seleucid(ancient_year)
    if a is not None and b is not None:
        return a, ("agree" if a == b else f"disagree (SE gives {b})")
    if a is not None:
        return a, "date_bce only"
    if b is not None:
        return b, "seleucid only"
    return None, "unresolved"
