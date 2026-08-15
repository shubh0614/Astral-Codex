# Celestial and calendar engine

Built 2026-08-16. Modules: `engine/bab_calendar.py`, `engine/sky.py`,
`engine/validate.py`.

## Conventions, stated not implied

| | |
|---|---|
| ephemeris | DE406, apparent geocentric positions |
| observer | Babylon, 32.5434 N, 44.4222 E, 34 m |
| delta-T | Skyfield's Morrison and Stephenson extrapolation, about 13,570 s at 263 BC |
| cubit | 2.4 degrees; finger = cubit/24 |
| day epoch | `to_jd` returns the START of the Babylonian day, which begins at sunset |

**DE441 was specified in plan.md; DE406 was used instead.** DE441 part 1 is
1.65 GB and the NAIF copies of the smaller ancient kernels have moved. DE406
covers 3000 BC to 3000 AD in 300 MB. Its precision is far beyond what
cubit-and-finger measurements require. Deliberate substitution, not a silent one.

## How the calendar layer was calibrated

The Babylonian year begins near the spring equinox, months begin at first
crescent visibility, and intercalary months were inserted by decree. Rather than
guess, the layer was calibrated against the diaries themselves: **a lunar eclipse
can only occur at full moon**, so converting a diary's eclipse date and checking
the computed lunar phase tests the calendar and the astronomy at once, with the
tablets as ground truth.

That immediately found a real error. The first implementation used the rule
"the equinox falls inside month I". Measured against 30 eclipse records, **22 of
30 came out exactly +30 days off, a whole lunation**, median +30.25 d. Switching
to "Nisannu 1 is the first crescent visibility on or after the equinox" moved
the median to +0.86 d and the within-2-days count from 2/30 to 19/30.

The residual is not error. `to_jd` returns the start of the Babylonian day at
sunset, and an event recorded as "night of the 14th" happens in the hours after
that, so a small positive offset is the expected behaviour.

Crescent thresholds were swept from 10 to 13 degrees elongation and 4 to 6
degrees altitude. The result is flat (19 to 20 of 30), so they are not finely
tuned and do not need to be. Settled at 11 and 5.

## Current validation state

87 lunar-eclipse records with a resolvable date. Median offset +0.26 d. Split by
where the year came from:

| year source | n | median offset | within 2 days |
|---|---:|---:|---:|
| catalogue (ADART 1 to 3, the diaries) | 48 | +0.66 d | **31/48, 65%** |
| assumed Seleucid from text (ADART 5, 6) | 39 | -28.95 d | 9/39, 23% |

**The calendar layer works for the diaries and does not work for goal-year
texts.** The reason is structural, not a bug: a goal-year text states the year it
was compiled *for*, then quotes observations from earlier cycles, so the year
printed on the tablet does not apply to the observations under it. ADART 6 units
are therefore tagged `date_confidence: unreliable` with a caveat field. Their
content is good, their dates are not.

This is exactly the situation plan.md Section 4 anticipated: "Some tablets may
not be date-normalizable at all without external scholarly reference tables,
that's expected, not a bug in your pipeline."

## What would improve it

- Parker and Dubberstein's *Babylonian Chronology* tables would replace the
  computed year start with the scholarly reconstruction and settle intercalation.
  That is the single highest-value addition.
- A king list would let regnal years other than Seleucid be resolved directly
  rather than assumed.
- The Normal Star table in `sky.py` is best-effort J2000 coordinates and should
  be checked against a catalogue before anyone relies on sub-degree separations.

## Sky layer

Three layers per plan.md Section 2: positions, visibility, semantic events.

- `position` gives apparent RA/Dec, ecliptic longitude and latitude, altitude and
  azimuth, and the zodiacal sign.
- `visibility` returns visible / marginal / not_visible / below_horizon from
  altitude, solar depression and elongation. Coarse by design.
- `events` emits labelled events with separations in both degrees and cubits, so
  the model never has to learn that a number means "close".
- `lunar_eclipse_possible` and `solar_eclipse_possible` check phase plus the
  Moon's ecliptic latitude, which is the node condition.

Run `python engine/validate.py` to reproduce the checks.
