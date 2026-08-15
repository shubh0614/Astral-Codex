"""
Measure register, which score_baseline.py cannot see.

The fact scorer checks that the right objects, measurements and relations
survive. It says nothing about whether the output SOUNDS like the diaries, and
register is the only open question left: few-shot already gets the facts right.

This counts concrete, checkable markers of the Sachs and Hunger register in the
generated text and in the reference it was supposed to match, then reports the
gap. Nothing here is a judgement call.

usage: python scripts/score_register.py data/processed/finetune_test_sample.json
"""

import json
import re
import sys
from pathlib import Path

# Things the diaries do. Present in the reference, wanted in the generation.
DIARY = {
    "first person non-observation": r"\bI did not watch\b|\bI watched\b|\bI did not see\b",
    "watch phrase": (r"\b(beginning of the night|first part of the night|"
                     r"middle part of the night|last part of the night)\b"),
    "'it stood' construction": r"\bit stood\b",
    "'having passed' construction": r"\bhaving passed\b",
    "'being N cubits' latitude": r"\bbeing\s+[\d½⅓⅔¼/ ]+\s*(cubits?|fingers?)\b",
    "cubit or finger units": r"\b(cubits?|fingers?)\b",
    "degree sign": r"°",
    "'measured' qualifier": r"\bmeasured\b",
    "semicolon clause joining": r";",
    "month roman numeral": r"\bMonth\s+[IVX]+",
    "ordinal night dating": r"\b(Night of the|The)\s+\d{1,2}(st|nd|rd|th)\b",
}

# Things the diaries do NOT do. Present here means modern drift.
MODERN = {
    "'not observed' for 'I did not watch'": r"\bnot observed\b|\bwas not observed\b",
    "'in magnitude'": r"\bin magnitude\b",
    "'approximately' or 'about'": r"\b(approximately|roughly)\b",
    "'degrees' spelled out": r"\bdegrees\b",
    "state syntax leaking": r"\bconfidence:\s*(high|medium|low)\b|\bobserved:\s",
    "explanatory aside": r"\b(which means|that is to say|in other words)\b",
    "bulleted output": r"(?m)^\s*[-*•]\s",
}


def count(patterns, text):
    return {k: len(re.findall(v, text, re.I)) for k, v in patterns.items()}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    rows = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if isinstance(rows, dict):
        rows = rows.get("test_sample") or rows.get("rows") or []
    if not rows:
        print("no test_sample rows found")
        sys.exit(1)

    ref = " \n".join(r["reference"] for r in rows)
    gen = " \n".join(r["generated"] for r in rows)

    print(f"{len(rows)} pairs\n")
    print(f"{'diary marker':38s} {'reference':>10} {'generated':>10}  verdict")
    print("-" * 76)
    rc, gc = count(DIARY, ref), count(DIARY, gen)
    kept = missed = 0
    for k in DIARY:
        r, g = rc[k], gc[k]
        if r == 0:
            verdict = "n/a in refs"
        elif g >= r * 0.6:
            verdict = "kept"
            kept += 1
        elif g == 0:
            verdict = "LOST"
            missed += 1
        else:
            verdict = "thin"
            missed += 1
        print(f"{k:38s} {r:>10} {g:>10}  {verdict}")

    print(f"\n{'modern drift marker':38s} {'reference':>10} {'generated':>10}  verdict")
    print("-" * 76)
    rm, gm = count(MODERN, ref), count(MODERN, gen)
    drift = 0
    for k in MODERN:
        r, g = rm[k], gm[k]
        v = "clean" if g == 0 else ("DRIFT" if r == 0 else "present in both")
        drift += 1 if (g > 0 and r == 0) else 0
        print(f"{k:38s} {r:>10} {g:>10}  {v}")

    # length discipline: the diaries are terse
    rl = sum(len(r["reference"].split()) for r in rows) / len(rows)
    gl = sum(len(r["generated"].split()) for r in rows) / len(rows)
    print(f"\nmean words per entry   reference {rl:.1f}   generated {gl:.1f}   "
          f"ratio {gl/rl:.2f}")

    print(f"\nmarkers kept {kept}, thin or lost {missed}, modern drift types {drift}")
    if missed == 0 and drift == 0:
        print("VERDICT: register preserved on every checkable marker")
    elif drift > 2 or missed > 3:
        print("VERDICT: register is drifting. This is the thing fine-tuning was "
              "supposed to fix, so it is the number that decides the run.")
    else:
        print("VERDICT: mostly preserved, with specific gaps listed above")


if __name__ == "__main__":
    main()
