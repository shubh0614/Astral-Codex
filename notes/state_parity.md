# Engine state vs training state (2026-08-19)

C1 from the checklist: does the OBSERVATION_STATE the engine produces match the
one the model was trained on? Reproduce with `python scripts/check_state_parity.py`.

**No. They share two fields out of thirteen.** This was flagged as the largest
untested risk in the project and it turns out to be real and large.

## What the model was trained to receive

```
<OBSERVATION_STATE>
  Date: year AlexanderIV 8, month I, day 8
  Watch: beginning of the night
  moon: observed
  alpha Leonis: observed
  Events: [{"event": "conjunction", "objects": ["moon", "alpha Leonis"],
            "relation": "behind", "separation": "2 1/2 cubits"}]
</OBSERVATION_STATE>
```

## What the engine produces today

```
{"event": "conjunction", "objects": ["venus", "eta Tauri"],
 "separation_deg": 1.325, "separation_cubits": 0.55}
```

## The gaps

**Event types: 663 of 1194 training events (56%) are types the engine cannot
produce.** Only `conjunction` overlaps.

| event type | training | engine |
|---|---:|---|
| conjunction | 531 | yes |
| lunar_six | 195 | no |
| latitude | 145 | no |
| last_appearance | 131 | no |
| first_appearance | 110 | no |
| eclipse | 41 | no |
| stationary_point | 15 | no |
| motion | 15 | no |
| acronychal_rising | 11 | no |

The engine can also emit `close_conjunction`, `full_moon` and `new_moon`, none of
which appear in training at all. Feeding those in would be an unseen token
sequence at inference.

**Event fields: the engine supplies 2 of 11.** `event` and `objects`. Missing:
`relation`, `separation`, `direction`, `sign`, `interval`, `value`, `offset`,
`passed`, `station_direction`. It adds two the model has never seen,
`separation_deg` and `separation_cubits`.

**`relation` is the one that matters most.** 531 training events carry it, all
four values (in front of, below, behind, above), and scorer criterion (f) exists
specifically to check it survives. The engine reports distance with no direction,
so on the current wiring the model would receive a conjunction with no relation
and have to invent one. That is exactly the failure mode the whole project is
built to prevent.

**Object naming does not match.** Engine writes `venus`, training writes `Venus`.
`moon` matches by luck.

**Seven stars in training are not in the engine's table:** Sirius (9 events),
eta Cancri (4), pi Scorpii (3), beta Leonis (1), plus three that are extraction
bugs rather than real stars: `beta Arieits`, `theta Ophighuchigh`, and `ϱ Leonis`
(a variant rho glyph `spell_greek` does not catch).

**`Watch` (441 states) and `Conditions` (176 states) have no engine source.**

## What is actually hard, and what is only unbuilt

Most of the above is unbuilt rather than impossible, and separating the two is
the useful part of this exercise:

**Computable, just not written yet:**
- `relation`: ecliptic longitude difference gives in front of and behind,
  ecliptic latitude difference gives above and below. The positions are already
  returned by `Sky.position`.
- `separation` as a Babylonian string: a formatter over `separation_cubits`.
  Training uses halves of cubits and whole fingers, nothing finer.
- `first_appearance`, `last_appearance`, `stationary_point`, `acronychal_rising`:
  standard phenomena, and the visibility layer already has the elongation test
  the first two need.
- `lunar_six`: timed intervals between rise and set events. `Sky.sunset` exists;
  the rest are the same almanac call.
- `sign`: already returned by `Sky.position`.
- `Watch`: the diaries' night watches are clock divisions, derivable from sunset
  and sunrise.

**Not computable at all:**
- `Conditions`. "clouds, I did not watch" is weather. No ephemeris has it. 176
  training states carry it, so the bridge has to decide what to emit at
  inference, and the honest options are to omit the line or to let the caller
  supply it. It must not be defaulted to "clear" silently, since that is the
  model inventing an observation.

## What this means for the plan

Nothing here contradicts plan.md. Section 2's two-layer engine and Calendar
Normalization Layer are exactly the right shape; the layers just have not been
extended to cover the event vocabulary the corpus actually uses, because the
event vocabulary was derived from the corpus afterwards.

**The order was wrong, not the design.** The training set was built from diary
text first and the engine second, so the engine was written against what seemed
reasonable rather than against the schema the model would be trained on. Building
the bridge now closes that, and the parity script should be re-run whenever
either side changes.

## Next

Build `engine/state.py`: JD in, a training-format OBSERVATION_STATE out, with an
explicit list of what it could not fill rather than silent omission. Then C2, an
end-to-end run on one real Babylonian night, which is the first time the engine
and the model will ever have been connected.
