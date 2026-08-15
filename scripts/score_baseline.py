"""
Score baseline outputs against the plan.md Section 7 pass criteria.

Per case, all of these must hold:
  (a) mentions every object present in the OBSERVATION_STATE
  (b) mentions no object absent from it
  (c) reads as a single dated entry, not a list of facts
  (d) stays inside the observation genre -- no invented omen or prediction
  (e) preserves the quantitative/qualitative hard facts, not just object names

4/5 passing -> proceed to Phase 1.
<=1/5 passing -> the prompt needs work before any fine-tuning discussion.

DEVIATION FROM THE LITERAL GATE TEXT, FLAGGED NOT HIDDEN
--------------------------------------------------------
plan.md Section 7 lists only (a), (b) and (c). Criterion (d) was added after
the scorer self-test surfaced the gap: an output reading

    "The 13th, Venus' first appearance in the east in Scorpius; this portends
     that the king will fall and there will be war."

satisfies (a), (b) and (c) completely -- every hard fact preserved, no extra
objects, one dated prose entry -- and would have PASSED the gate as written,
while being exactly the failure the guardrail exists to prevent. It is an
observation-genre prompt inventing an omen.

This is not a new architectural idea; plan.md already treats the boundary as
first-class. Section 2 proposes training on negative examples "under
<GENRE=OBSERVATION>, explicitly train against adding interpretive claims that
don't belong to that genre", and Section 8 test C is genre fidelity. The gate
checklist simply never enumerated it. Added here rather than silently omitted,
same as the >2-sentence issue in segment_babylonian.py.

Criterion (e) was added for the same reason, after the non-LLM template control
scored 5/5 while silently dropping the watch ("beginning of the night"), the
latitude clause ("the moon being 1 cubit high to the north"), the month number,
"earthshine" and the direction "in the east" -- every one of them a hard fact
sitting in the OBSERVATION_STATE. Criterion (a) checks only object NAMES, so a
model can discard every measurement and still pass. For a project whose whole
premise is that hard facts must never change, that is the wrong thing to
measure.

(a) and (b) are fully mechanical and are the load-bearing part -- this is the
deterministic whitelist that plan.md Section 2 puts ABOVE LLM-as-judge in the
validation hierarchy. (c) is partly a judgement call, so it is heuristic here
and carries a human_override field; the heuristic only checks the things that
can be checked (a date marker is present, the output is prose rather than
bullets, the length is entry-like).

usage: python scripts/score_baseline.py <outputs.json>
       outputs.json = {"model": "...", "tier": "few-shot", "outputs": {case_id: text}}
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data" / "processed" / "baseline_cases.json"

DATE_MARKER = re.compile(
    r"\b(night of the|the)\s+\d{1,2}(st|nd|rd|th)\b|\bmonth\s+[IVX]+\b", re.I
)
BULLETY = re.compile(r"^\s*[-*•]|\n\s*[-*•]|^\s*\d+[.)]\s", re.M)
INTERPRETIVE = re.compile(
    r"\b(portend\w*|omen|foretell\w*|signif\w*|prophec\w*|shall come to pass|"
    r"means that|indicates that|the king will|there will be war)\b", re.I
)


def mentions(text, token):
    """Substring match, case-insensitive. Tokens are already lowercase stems."""
    return token.lower() in text.lower()


def score_case(case, output):
    t = output.strip()
    allowed_extra = [x.lower() for x in case.get("allowed_extra", [])]

    missing = [o for o in case["required_objects"] if not mentions(t, o)]
    hallucinated = [
        o for o in case["forbidden_objects"]
        if mentions(t, o) and o.lower() not in allowed_extra
    ]

    a = not missing
    b = not hallucinated

    has_date = bool(DATE_MARKER.search(t))
    is_bullets = bool(BULLETY.search(t))
    n_words = len(t.split())
    sane_len = 8 <= n_words <= 160
    c = has_date and not is_bullets and sane_len

    genre_leak = bool(INTERPRETIVE.search(t))
    d = not genre_leak

    # (e) the quantitative/qualitative hard facts survive, not just the names
    norm = re.sub(r"\s+", " ", t).lower()
    dropped = [
        alts[0] for alts in case.get("required_facts", [])
        if not any(v.lower() in norm for v in alts)
    ]
    e = not dropped

    # (f) the pairwise relation survives in the right ORDER: OBJ1 <rel> OBJ2.
    # Catches reversal and, more commonly, destruction of the pairing.
    rel_spec = case.get("required_relation")
    rel_ok, rel_detail = True, None
    if rel_spec:
        pat = (
            r"(?:%s)\b.{0,80}?\b(?:%s)\b.{0,60}?(?:%s)"
            % ("|".join(map(re.escape, rel_spec["first"])),
               "|".join(map(re.escape, rel_spec["relation"])),
               "|".join(map(re.escape, rel_spec["second"])))
        )
        rel_ok = bool(re.search(pat, norm, re.S))
        if not rel_ok:
            rel_detail = (f"expected '{rel_spec['first'][0]} ... "
                          f"{rel_spec['relation'][0]} ... {rel_spec['second'][0]}' "
                          f"in that order")

    return {
        "case": case["id"],
        "phenomenon": case["phenomenon"],
        "a_all_objects_present": a,
        "b_no_extra_objects": b,
        "c_reads_as_entry": c,
        "d_stays_in_observation_genre": d,
        "e_hard_facts_preserved": e,
        "dropped_facts": dropped,
        "f_relation_order_correct": rel_ok,
        "relation_detail": rel_detail,
        "pass": a and b and c and d and e and rel_ok,
        "missing_objects": missing,
        "hallucinated_objects": hallucinated,
        "c_detail": {
            "has_date_marker": has_date,
            "is_bulleted": is_bullets,
            "word_count": n_words,
            "length_ok": sane_len,
        },
        "genre_leak_interpretive_language": genre_leak,
        "human_override": None,
        "output": t,
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    runf = Path(sys.argv[1])
    run = json.loads(runf.read_text(encoding="utf-8"))
    # a run records which case file it used; fall back to the main set
    cpath = Path(run["cases_file"]) if run.get("cases_file") else CASES
    cases = {c["id"]: c for c in json.loads(cpath.read_text(encoding="utf-8"))["cases"]}

    results = []
    for cid, out in run["outputs"].items():
        if cid not in cases:
            print(f"  !! unknown case id {cid}, skipping")
            continue
        results.append(score_case(cases[cid], out))

    passed = sum(1 for r in results if r["pass"])
    n = len(results)

    print(f"model : {run.get('model','?')}")
    print(f"tier  : {run.get('tier','?')}")
    print(f"score : {passed}/{n}\n")
    for r in results:
        flag = "PASS" if r["pass"] else "FAIL"
        print(f"[{flag}] {r['case']:28s} a={int(r['a_all_objects_present'])} "
              f"b={int(r['b_no_extra_objects'])} c={int(r['c_reads_as_entry'])} "
              f"d={int(r['d_stays_in_observation_genre'])} "
              f"e={int(r['e_hard_facts_preserved'])} "
              f"f={int(r['f_relation_order_correct'])}")
        if r["relation_detail"]:
            print(f"         RELATION BROKEN: {r['relation_detail']}")
        if r["missing_objects"]:
            print(f"         missing: {r['missing_objects']}")
        if r["dropped_facts"]:
            print(f"         DROPPED FACTS: {r['dropped_facts']}")
        if r["hallucinated_objects"]:
            print(f"         HALLUCINATED: {r['hallucinated_objects']}")
        if r["genre_leak_interpretive_language"]:
            print(f"         genre leak: interpretive language in an observation entry")
        print(f"         > {r['output'][:150]}")

    print()
    if n and passed >= 4:
        print("VERDICT: passes the plan.md gate (>=4/5). Prompting may be sufficient;")
        print("         fine-tuning is NOT automatically justified. Compare against the")
        print("         non-LLM template baseline before committing GPU time.")
    elif passed <= 1:
        print("VERDICT: <=1/5. Per plan.md the PROMPT needs work before any")
        print("         fine-tuning discussion is worth having.")
    else:
        print(f"VERDICT: {passed}/{n} - middle band. Iterate the prompt once, re-run,")
        print("         and only then treat fine-tuning as justified.")

    outp = runf.with_name(runf.stem + "_scored.json")
    outp.write_text(json.dumps({
        "model": run.get("model"), "tier": run.get("tier"),
        "passed": passed, "total": n, "results": results,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {outp}")


if __name__ == "__main__":
    main()
