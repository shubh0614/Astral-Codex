"""
Sanity-check the baseline scorer before trusting it on model output.

Two fixtures:
  1. the real historical diary entries for the five cases -- these ARE the
     right answer, so a correct scorer must give them 5/5
  2. deliberately broken outputs (wrong planet, extra planet, bulleted list,
     omen language) -- a correct scorer must catch every one

A scorer that cannot tell these apart would silently decide whether this
project needs fine-tuning, so it gets tested first.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "data" / "processed" / "baseline_cases.json").read_text(encoding="utf-8"))["cases"]
TMP = ROOT / "data" / "processed"

GOOD = {c["id"]: c["reference_text"] for c in CASES}

BAD = {
    # wrong star swapped in, and Capricorni dropped
    "bab-01-moon-star":
        "Night of the 11th, beginning of the night, the moon was 1 cubit 8 fingers in front of α Tauri.",
    # extra planet hallucinated alongside the real one
    "bab-02-moon-planet":
        "Night of the 2nd, the moon was 1 1/2 cubits behind Jupiter, with Saturn nearby to the west.",
    # bulleted list of facts rather than an entry
    "bab-03-planet-planet":
        "- Venus: visible\n- Mars: visible\n- separation: 3 fingers",
    # omen language leaking into an observation-genre entry
    "bab-04-heliacal-rising":
        "The 13th, Venus' first appearance in the east in Scorpius; this portends that the king will fall and there will be war.",
    # required object missing entirely
    "bab-05-lunar-first-visibility":
        "The 1st, it was bright and low, and the night passed without cloud.",
}


def run(tag, outputs):
    p = TMP / f"baseline_run_{tag}.json"
    p.write_text(json.dumps(
        {"model": f"selftest-{tag}", "tier": "fixture", "outputs": outputs},
        indent=2, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "score_baseline.py"), str(p)],
        capture_output=True, text=True, encoding="utf-8",
    )
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr)
    scored = json.loads((TMP / f"baseline_run_{tag}_scored.json").read_text(encoding="utf-8"))
    return scored["passed"], scored["total"], scored


print("#" * 78)
print("# FIXTURE 1 - real historical entries. Must score 5/5.")
print("#" * 78)
g_pass, g_tot, _ = run("selftest_good", GOOD)

print("#" * 78)
print("# FIXTURE 2 - deliberately broken outputs. Must score 0/5.")
print("#" * 78)
b_pass, b_tot, b_scored = run("selftest_bad", BAD)

print("=" * 78)
ok = (g_pass == g_tot) and (b_pass == 0)
print(f"real entries      : {g_pass}/{g_tot}   (want {g_tot}/{g_tot})")
print(f"broken entries    : {b_pass}/{b_tot}   (want 0/{b_tot})")

# confirm each broken case failed for the RIGHT reason
reasons = {
    "bab-01-moon-star": "missing_objects",
    "bab-02-moon-planet": "hallucinated_objects",
    "bab-03-planet-planet": "c_reads_as_entry",
    "bab-04-heliacal-rising": "genre_leak_interpretive_language",
    "bab-05-lunar-first-visibility": "missing_objects",
}
print("\ncaught for the right reason?")
for r in b_scored["results"]:
    want = reasons[r["case"]]
    if want == "c_reads_as_entry":
        hit = not r["c_reads_as_entry"]
    elif want == "genre_leak_interpretive_language":
        hit = r["genre_leak_interpretive_language"]
    else:
        hit = bool(r[want])
    print(f"   {'yes' if hit else 'NO '}  {r['case']:30s} expected {want}")
    ok = ok and hit

print("\nSCORER SELF-TEST:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
