"""
Compare the OBSERVATION_STATE the model was trained on against the one the
engine can actually produce.

Every training state was derived from diary text by extract_states.py. At
inference they have to come from engine/sky.py instead. Nothing has ever checked
that those two produce the same thing, and if they do not the model breaks at the
exact moment it starts being used for real rather than evaluated.

This does not generate text. It reads the training states, reads what the engine
emits for a real date, and reports every field the model expects that the engine
cannot supply.

usage: python scripts/check_state_parity.py
"""

import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from engine.sky import NORMAL_STARS, PLANETS, Sky

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data" / "processed" / "train.jsonl"

# One real night with a conjunction in it, so events() returns something.
PROBE = (-330, 4, 20, 18, 0)


def training_vocabulary():
    labels, events, keys, rels, objects = (collections.Counter() for _ in range(5))
    for line in TRAIN.open(encoding="utf-8"):
        state = json.loads(line)["messages"][1]["content"]
        for ln in state.splitlines():
            m = re.match(r"\s*([A-Za-z][\w ]*):", ln)
            if m:
                labels[m.group(1)] += 1
        m = re.search(r"Events: (\[.*\])", state)
        if not m:
            continue
        for e in json.loads(m.group(1)):
            events[e.get("event")] += 1
            for k in e:
                keys[k] += 1
            if e.get("relation"):
                rels[e["relation"]] += 1
            for o in e.get("objects", []):
                objects[o] += 1
    return labels, events, keys, rels, objects


def engine_vocabulary():
    sky = Sky()
    jd = sky.ts.utc(*PROBE).tt
    evs = sky.events(jd)
    keys, events, objects = (collections.Counter() for _ in range(3))
    for e in evs:
        events[e["event"]] += 1
        for k in e:
            keys[k] += 1
        for o in e["objects"]:
            objects[o] += 1
    # events() cannot emit these but the code paths exist, so count them as
    # reachable rather than pretending the engine has nothing to say.
    reachable = set(events) | {"full_moon", "new_moon", "close_conjunction"}
    return keys, events, objects, reachable, jd, evs


def section(t):
    print()
    print("=" * 70)
    print(t)
    print("=" * 70)


def main():
    labels, t_events, t_keys, t_rels, t_objects = training_vocabulary()
    e_keys, e_events, e_objects, e_reachable, jd, raw = engine_vocabulary()

    section("what the engine emits, raw")
    print(f"probe JD {jd:.4f}")
    print(json.dumps(raw[:2], indent=1))

    section("1. event types")
    print(f"{'event type':22s} {'in training':>12} {'engine can emit':>18}")
    print("-" * 56)
    missing_events = 0
    for ev, n in t_events.most_common():
        ok = ev in e_reachable
        if not ok:
            missing_events += n
        print(f"{ev:22s} {n:>12} {'yes' if ok else 'NO':>18}")
    for ev in sorted(e_reachable - set(t_events)):
        print(f"{ev:22s} {0:>12} {'yes, never trained':>18}")
    share = missing_events / max(sum(t_events.values()), 1)
    print(f"\n{missing_events} of {sum(t_events.values())} training events "
          f"({share:.0%}) are of a type the engine cannot produce.")

    section("2. event fields")
    print(f"{'field':22s} {'in training':>12} {'engine emits':>14}")
    print("-" * 52)
    for k, n in t_keys.most_common():
        print(f"{k:22s} {n:>12} {'yes' if k in e_keys else 'NO':>14}")
    for k in sorted(set(e_keys) - set(t_keys)):
        print(f"{k:22s} {0:>12} {'yes, unseen':>14}")

    section("3. relation vocabulary")
    print("training relations:", ", ".join(f"{k} ({v})" for k, v in t_rels.most_common()))
    print("engine relations  : none. events() reports separation only, with no "
          "above/below/in front of/behind.")
    print(f"\n{sum(t_rels.values())} training events carry a relation. Scorer "
          "criterion (f) checks it.")

    section("4. object naming")
    t_bodies = {o for o in t_objects if o.lower() in PLANETS or o.lower() in ("moon", "sun")}
    e_bodies = {o for o in e_objects}
    print(f"training writes planets as : {sorted(t_bodies)[:6]}")
    print(f"engine writes planets as   : {sorted(b for b in e_bodies if b in PLANETS)}")
    t_stars = {o for o in t_objects if o not in t_bodies}
    unknown = sorted(s for s in t_stars if s not in NORMAL_STARS)
    print(f"\ntraining stars not in the engine's NORMAL_STARS table ({len(unknown)}):")
    for s in unknown:
        print(f"  {s:24s} {t_objects[s]:>4} training events")

    section("5. state line labels")
    engine_can = {"Date", "Events"}
    for lab, n in labels.most_common():
        if lab in ("Date", "Events", "Watch", "Conditions"):
            print(f"{lab:22s} {n:>6}  "
                  f"{'engine supplies' if lab in engine_can else 'ENGINE HAS NO SOURCE'}")

    section("verdict")
    print("The engine and the training data do not share a state format. The gaps")
    print("are not cosmetic: relation, the Babylonian separation string, the watch")
    print("and every event type except conjunction have no engine source at all.")
    print("A bridge module has to build the state, and where it cannot, the")
    print("difference has to be visible rather than silently absent.")


if __name__ == "__main__":
    main()
