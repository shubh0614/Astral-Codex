"""
Celestial engine: physical state, visibility, and semantic events.

Three layers, per plan.md Section 2:
  positions   apparent geocentric RA/Dec and ecliptic coordinates
  visibility  altitude, solar depression and elongation -> visible/marginal/not
  events      labelled events the LLM conditions on, e.g. close_conjunction

Conventions, stated rather than implied:
  ephemeris   DE406, apparent geocentric positions
  observer    Babylon, 32.5434 N, 44.4222 E
  delta-T     Skyfield's built-in Morrison and Stephenson extrapolation
  units       separations in degrees; 1 Babylonian cubit is taken as 2.4 degrees
"""

from functools import lru_cache

from skyfield import almanac
from skyfield.api import Star, load, load_file, wgs84
from skyfield.framelib import ecliptic_frame

EPH_PATH = "engine/ephem/de406.bsp"
BABYLON = wgs84.latlon(32.5434, 44.4222, elevation_m=34)
CUBIT_DEG = 2.4
FINGER_DEG = CUBIT_DEG / 24.0

PLANETS = {
    "mercury": "mercury", "venus": "venus", "mars": "mars",
    "jupiter": "jupiter barycenter", "saturn": "saturn barycenter",
}

# Babylonian Normal Stars, the reference points the diaries measure against.
# J2000 RA (hours) / Dec (degrees). Best-effort table, verify against a
# catalogue before relying on sub-degree results.
NORMAL_STARS = {
    "eta Piscium": (1.5247, 15.3458), "beta Arietis": (1.9107, 20.8081),
    "alpha Arietis": (2.1195, 23.4628), "eta Tauri": (3.7914, 24.1051),
    "alpha Tauri": (4.5987, 16.5093), "beta Tauri": (5.4382, 28.6075),
    "zeta Tauri": (5.6274, 21.1425), "eta Geminorum": (6.2480, 22.5067),
    "mu Geminorum": (6.3827, 22.5136), "gamma Geminorum": (6.6285, 16.3993),
    "alpha Geminorum": (7.5766, 31.8883), "beta Geminorum": (7.7553, 28.0262),
    "gamma Cancri": (8.7214, 21.4686), "delta Cancri": (8.7447, 18.1543),
    "epsilon Leonis": (9.7642, 23.7743), "alpha Leonis": (10.1395, 11.9672),
    "rho Leonis": (10.5468, 9.3067), "theta Leonis": (11.2351, 15.4297),
    "beta Virginis": (11.8449, 1.7647), "gamma Virginis": (12.6943, -1.4494),
    "alpha Virginis": (13.4199, -11.1613), "alpha Librae": (14.8479, -16.0418),
    "beta Librae": (15.2833, -9.3829), "delta Scorpii": (16.0056, -22.6217),
    "beta Scorpii": (16.0906, -19.8056), "alpha Scorpii": (16.4901, -26.4319),
    "theta Ophiuchi": (17.3668, -24.9994), "beta Capricorni": (20.3502, -14.7814),
    "gamma Capricorni": (21.6682, -16.6623), "delta Capricorni": (21.7840, -16.1273),
}

ZODIAC = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpius", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]


class Sky:
    def __init__(self, eph_path=EPH_PATH):
        self.eph = load_file(eph_path)
        self.ts = load.timescale()
        self.earth = self.eph["earth"]
        self.observer = self.earth + BABYLON

    def _body(self, name):
        n = name.lower().strip()
        if n in ("sun", "moon"):
            return self.eph[n]
        if n in PLANETS:
            return self.eph[PLANETS[n]]
        if name in NORMAL_STARS:
            ra, dec = NORMAL_STARS[name]
            return Star(ra_hours=ra, dec_degrees=dec)
        raise KeyError(f"unknown body {name!r}")

    def at(self, jd):
        return self.ts.tt_jd(jd)

    def position(self, name, jd, topocentric=True):
        t = self.at(jd)
        origin = self.observer if topocentric else self.earth
        p = origin.at(t).observe(self._body(name)).apparent()
        ra, dec, _ = p.radec()
        lat, lon, _ = p.frame_latlon(ecliptic_frame)
        out = {
            "body": name,
            "ra_hours": ra.hours,
            "dec_deg": dec.degrees,
            "ecliptic_lon_deg": lon.degrees % 360,
            "ecliptic_lat_deg": lat.degrees,
            "sign": ZODIAC[int((lon.degrees % 360) // 30)],
        }
        if topocentric:
            alt, az, _ = p.altaz()
            out["altitude_deg"] = alt.degrees
            out["azimuth_deg"] = az.degrees
        return out

    def separation_deg(self, a, b, jd):
        t = self.at(jd)
        o = self.observer.at(t)
        return o.observe(self._body(a)).apparent().separation_from(
            o.observe(self._body(b)).apparent()).degrees

    def elongation_deg(self, name, jd):
        return self.separation_deg(name, "sun", jd)

    def moon_phase_deg(self, jd):
        """0 new, 180 full."""
        return self.elongation_deg("moon", jd)

    def visibility(self, name, jd):
        """Coarse visible / marginal / not_visible, per plan.md's visibility layer."""
        p = self.position(name, jd)
        sun_alt = self.position("sun", jd)["altitude_deg"]
        elong = self.elongation_deg(name, jd) if name != "sun" else 0.0
        if p["altitude_deg"] < 0:
            state = "below_horizon"
        elif sun_alt > -6:
            state = "not_visible" if name != "moon" else "marginal"
        elif elong < 10:
            state = "not_visible"
        elif elong < 15 or p["altitude_deg"] < 5:
            state = "marginal"
        else:
            state = "visible"
        return {"state": state, "altitude_deg": p["altitude_deg"],
                "solar_altitude_deg": sun_alt, "elongation_deg": elong}

    def sunset(self, jd):
        y, m, d = self.ts.tt_jd(jd).tt_calendar()[:3]
        t0, t1 = self.ts.tt(y, m, d, 0), self.ts.tt(y, m, d + 2, 0)
        t, up = almanac.find_discrete(t0, t1, almanac.sunrise_sunset(self.eph, BABYLON))
        s = t[up == 0]
        return s[0].tt if len(s) else None

    def events(self, jd, bodies=None, conjunction_deg=3.0):
        """Semantic events the LLM can condition on directly."""
        bodies = bodies or (["moon", "sun"] + list(PLANETS))
        out = []
        moving = [b for b in bodies if b != "sun"]
        for i, a in enumerate(moving):
            for b in moving[i + 1:]:
                s = self.separation_deg(a, b, jd)
                if s <= conjunction_deg:
                    out.append({
                        "event": "close_conjunction" if s <= 1.5 else "conjunction",
                        "objects": [a, b], "separation_deg": round(s, 3),
                        "separation_cubits": round(s / CUBIT_DEG, 2),
                    })
        for b in moving:
            if b == "moon":
                continue
            for star, _ in NORMAL_STARS.items():
                s = self.separation_deg(b, star, jd)
                if s <= conjunction_deg:
                    out.append({"event": "conjunction", "objects": [b, star],
                                "separation_deg": round(s, 3),
                                "separation_cubits": round(s / CUBIT_DEG, 2)})
        ph = self.moon_phase_deg(jd)
        if ph > 177:
            out.append({"event": "full_moon", "objects": ["moon"],
                        "elongation_deg": round(ph, 2)})
        if ph < 3:
            out.append({"event": "new_moon", "objects": ["moon"],
                        "elongation_deg": round(ph, 2)})
        return out

    def lunar_eclipse_possible(self, jd, lat_limit=1.5):
        """Full moon within `lat_limit` degrees of the ecliptic means the Moon is
        near a node, which is the condition for a lunar eclipse."""
        ph = self.moon_phase_deg(jd)
        beta = abs(self.position("moon", jd, topocentric=False)["ecliptic_lat_deg"])
        return {"full_moon": ph > 177, "phase_deg": round(ph, 2),
                "moon_ecliptic_lat_deg": round(beta, 3),
                "eclipse_possible": ph > 177 and beta < lat_limit}

    def solar_eclipse_possible(self, jd, lat_limit=1.5):
        ph = self.moon_phase_deg(jd)
        beta = abs(self.position("moon", jd, topocentric=False)["ecliptic_lat_deg"])
        return {"new_moon": ph < 3, "phase_deg": round(ph, 2),
                "moon_ecliptic_lat_deg": round(beta, 3),
                "eclipse_possible": ph < 3 and beta < lat_limit}
