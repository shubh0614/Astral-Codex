"""
Build the QLoRA training set from the extracted states.

Decisions made here, and why:

  zero-gap only      entries still carrying [...] would teach the model to emit
                     tablet damage as a stylistic tic (plan.md Section 4)
  drop goal-year     ADART 6 dates are unreliable for a structural reason, see
                     notes/engine.md. Their text is fine but a wrong date paired
                     with a right entry is a lie in the training data
  stratify           conjunctions are 61% of the corpus. Left alone the model
                     learns one phenomenon and ignores stationary points and
                     eclipses, which is what the ADART 5/6 fetch was meant to fix
  split by TABLET    units from one tablet share phrasing and dates, so a random
                     unit-level split leaks the test set into training
  quarantine         the 9 baseline evaluation cases are removed by source text
                     id so the fine-tune cannot be scored on what it trained on

Output: data/processed/train.jsonl, val.jsonl, test.jsonl, plus a data card.
"""

import collections
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATES = ROOT / "data" / "processed" / "babylonian_states.json"
CASES = ROOT / "data" / "processed" / "baseline_cases.json"
GEN_CASES = ROOT / "data" / "processed" / "baseline_cases_generalization.json"
OUTDIR = ROOT / "data" / "processed"

SEED = 20260816
CAP = {"conjunction": 400, "lunar_six": 220}
VAL_FRAC, TEST_FRAC = 0.10, 0.10

SYSTEM = (
    "You are reproducing the register of the Babylonian Astronomical Diaries "
    "as rendered in the Sachs and Hunger English translation. Write ONE dated "
    "diary entry describing exactly the sky state given. Mention every object "
    "in the state and no others, preserve the measurements and relations "
    "exactly, write continuous prose in the diary's voice, and add no omens or "
    "interpretation."
)


def primary(rec):
    """One label per example, rarest event wins so rare phenomena survive."""
    order = ["eclipse", "acronychal_rising", "stationary_point",
             "first_appearance", "last_appearance", "motion", "latitude",
             "lunar_six", "conjunction"]
    kinds = {e["event"] for e in rec["events"]}
    for k in order:
        if k in kinds:
            return k
    return "other"


def strip_year(state):
    """Drop the 'year ...' clause from the Date line, keeping month and day."""
    out = []
    for line in state.split("\n"):
        if line.startswith("  Date:"):
            parts = [p for p in line[len("  Date:"):].split(",")
                     if "year" not in p]
            line = "  Date:" + ",".join(parts) if parts else "  Date: unknown"
        out.append(line)
    return "\n".join(out)


def quarantined_text_ids():
    ids = set()
    for p in (CASES, GEN_CASES):
        for c in json.loads(p.read_text(encoding="utf-8"))["cases"]:
            src = c.get("source", {})
            if src.get("text_id"):
                ids.add(src["text_id"])
            if src.get("designation"):
                ids.add(src["designation"])
    return ids


def main():
    rng = random.Random(SEED)
    recs = json.loads(STATES.read_text(encoding="utf-8"))
    quarantine = quarantined_text_ids()

    kept = []
    why, adjusted = collections.Counter(), collections.Counter()
    for r in recs:
        if r["gaps"] != 0:
            why["has tablet-damage gaps"] += 1
            continue
        if r["text_id"] in quarantine or r["designation"] in quarantine:
            why["quarantined evaluation source"] += 1
            continue
        if r.get("date_confidence") == "unreliable":
            # Goal-year texts: only the YEAR is untrustworthy. The month and day
            # come from in-text markers and the entry itself, so the example is
            # kept with the year stripped from the state rather than thrown away.
            if not r.get("month"):
                why["goal-year text with no month either"] += 1
                continue
            r = dict(r, state=strip_year(r["state"]), year_omitted=True)
            adjusted["goal-year, kept with the year stripped"] += 1
        kept.append(r)

    before = collections.Counter(primary(r) for r in kept)

    by_class = collections.defaultdict(list)
    for r in kept:
        by_class[primary(r)].append(r)
    balanced = []
    for cls, rows in by_class.items():
        rng.shuffle(rows)
        balanced.extend(rows[:CAP.get(cls, len(rows))])
    after = collections.Counter(primary(r) for r in balanced)

    # split by tablet so near-duplicate units cannot straddle the split
    tablets = sorted({r["text_id"] for r in balanced})
    rng.shuffle(tablets)
    n_val = max(1, int(len(tablets) * VAL_FRAC))
    n_test = max(1, int(len(tablets) * TEST_FRAC))
    val_t = set(tablets[:n_val])
    test_t = set(tablets[n_val:n_val + n_test])

    splits = {"train": [], "val": [], "test": []}
    for r in balanced:
        s = "val" if r["text_id"] in val_t else "test" if r["text_id"] in test_t else "train"
        splits[s].append({
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": r["state"]},
                {"role": "assistant", "content": r["entry"]},
            ],
            "meta": {"text_id": r["text_id"], "volume": r["volume"],
                     "designation": r["designation"], "class": primary(r),
                     "date_confidence": r.get("date_confidence")},
        })

    for name, rows in splits.items():
        p = OUTDIR / f"{name}.jsonl"
        p.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows),
                     encoding="utf-8")

    tok = sum(len(x["messages"][2]["content"]) for x in splits["train"]) // 4
    card = {
        "built": "2026-08-16",
        "seed": SEED,
        "source": "ORACC ADsD ADART 1,2,3,5 via data/processed/babylonian_states.json",
        "excluded": dict(why),
        "adjusted_not_excluded": dict(adjusted),
        "class_mix_before_balancing": dict(before.most_common()),
        "class_mix_after_balancing": dict(after.most_common()),
        "caps_applied": CAP,
        "split_unit": "tablet (text_id), not observation, to prevent leakage",
        "counts": {k: len(v) for k, v in splits.items()},
        "tablets": {"total": len(tablets), "val": len(val_t), "test": len(test_t)},
        "approx_target_tokens_train": tok,
        "quarantined_sources": sorted(quarantine),
        "known_limits": [
            "Target text is a modern English translation, so the register learned "
            "is Sachs and Hunger's, not Akkadian. plan.md Section 1 already frames "
            "the project this way.",
            "States are derived from the entry text, not computed by the engine. "
            "At inference the state will come from the engine, so any format drift "
            "between the two will show up as a distribution shift.",
            f"Only {tok} approximate target tokens. Small enough that overfitting "
            "is the main risk; keep LoRA rank modest and watch validation loss.",
        ],
    }
    (OUTDIR / "training_set_card.json").write_text(
        json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"states available : {len(recs)}")
    for k, v in why.most_common():
        print(f"  excluded, {k}: {v}")
    for k, v in adjusted.most_common():
        print(f"  kept but adjusted, {k}: {v}")
    print(f"eligible         : {len(kept)}")
    print(f"after balancing  : {len(balanced)}")
    print(f"\nclass mix   {'before':>8} {'after':>8}")
    for k in sorted(before, key=lambda x: -before[x]):
        print(f"   {k:20s} {before[k]:8d} {after.get(k,0):8d}")
    print(f"\nsplit by tablet ({len(tablets)} tablets)")
    for k, v in splits.items():
        print(f"   {k:6s} {len(v):5d} examples")
    print(f"\napprox target tokens in train: {tok:,}")
    print(f"-> {OUTDIR}/train.jsonl, val.jsonl, test.jsonl, training_set_card.json")


if __name__ == "__main__":
    main()
