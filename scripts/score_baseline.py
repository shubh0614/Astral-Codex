"""
Score baseline outputs against the plan.md Section 7 gate. All must hold:
  (a) mentions every object in the OBSERVATION_STATE
  (b) mentions no object absent from it
  (c) reads as a single dated entry, not a list of facts
  (d) stays in the observation genre, no invented omen
  (e) preserves the measurements, not just the object names
  (f) keeps the pairwise relation in the right order

plan.md lists only (a) to (c). Why (d), (e) and (f) were added is in
notes/baseline_gate.md.

usage: python scripts/score_baseline.py <run.json>
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
# Degeneration: state syntax bleeding into prose, unfilled placeholders, or the
# model looping. All three were produced by the 7B run and all three passed the
# checks above, which is why criterion (g) exists.
DEGENERATE = {
    "state syntax in prose": re.compile(
        r"\b(high|medium|low)\s+confidence\b|\bconfidence:\s*(high|medium|low)\b"
        r"|\bobserved:\s|\bEvents:\s*\[", re.I),
    "unfilled placeholder": re.compile(r"\bthe\s+xth\b|\bnn\b|\[x\]|\bx°", re.I),
}
# A star is not interchangeable with another star of the same constellation.
# The 7B invented "alpha Virginis" for a state naming "beta Virginis" and passed,
# because the object whitelist only sees "Virginis".
GREEK_TOKEN = re.compile(
    r"\b(alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|"
    r"xi|omicron|rho|sigma|tau|upsilon|phi|chi|psi|omega)\s+([A-Z][a-z]+)", re.I)
GREEK_LETTER = {"α": "alpha", "β": "beta", "γ": "gamma",
                "δ": "delta", "ε": "epsilon", "ζ": "zeta",
                "η": "eta", "θ": "theta", "ϑ": "theta",
                "μ": "mu", "ρ": "rho"}


def star_tokens(text):
    """Normalise 'beta Virginis' and 'beta Virginis' written with the letter."""
    t = text
    for g, name in GREEK_LETTER.items():
        t = t.replace(g, name + " ")
    return {f"{m.group(1).lower()} {m.group(2).lower()}"
            for m in GREEK_TOKEN.finditer(t)}


def mentions(text, token):
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

    norm = re.sub(r"\s+", " ", t).lower()
    dropped = [
        alts[0] for alts in case.get("required_facts", [])
        if not any(v.lower() in norm for v in alts)
    ]
    e = not dropped

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

    # (g) no degeneration, and no star swapped for another of the same
    # constellation
    deg = [k for k, rx in DEGENERATE.items() if rx.search(t)]
    state_stars = star_tokens(case["observation_state"])
    out_stars = star_tokens(t)
    invented_stars = sorted(out_stars - state_stars) if state_stars else []
    g = not deg and not invented_stars

    return {
        "case": case["id"],
        "phenomenon": case["phenomenon"],
        "g_no_degeneration": g,
        "degeneration": deg,
        "invented_stars": invented_stars,
        "a_all_objects_present": a,
        "b_no_extra_objects": b,
        "c_reads_as_entry": c,
        "d_stays_in_observation_genre": d,
        "e_hard_facts_preserved": e,
        "dropped_facts": dropped,
        "f_relation_order_correct": rel_ok,
        "relation_detail": rel_detail,
        "pass": a and b and c and d and e and rel_ok and g,
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
              f"f={int(r['f_relation_order_correct'])} "
              f"g={int(r['g_no_degeneration'])}")
        if r["relation_detail"]:
            print(f"         RELATION BROKEN: {r['relation_detail']}")
        if r["degeneration"]:
            print(f"         DEGENERATION: {', '.join(r['degeneration'])}")
        if r["invented_stars"]:
            print(f"         INVENTED STARS: {r['invented_stars']}")
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
