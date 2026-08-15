"""
Run the baseline cases against a model and write outputs for scoring.

No model runner or API key exists in this dev environment, so this supports
whichever backend turns up first. Easiest path on the GTX 1650 box is ollama
with a small model; a 7B at Q4 is borderline on 4 GB VRAM and will spill to CPU
but it will run.

  # ollama (local, no key)
  ollama pull qwen2.5:7b
  python scripts/run_baseline.py --backend ollama --model qwen2.5:7b

  # any OpenAI-compatible endpoint
  set OPENAI_API_KEY=...
  python scripts/run_baseline.py --backend openai --model gpt-4o-mini

  # anthropic
  set ANTHROPIC_API_KEY=...
  python scripts/run_baseline.py --backend anthropic --model claude-sonnet-5

  # the non-LLM control from plan.md Section 2 -- no model, pure template
  python scripts/run_baseline.py --backend template

  # zero-shot tier instead of few-shot
  python scripts/run_baseline.py --backend ollama --model qwen2.5:7b --shots 0

Then: python scripts/score_baseline.py data/processed/baseline_run_<tag>.json
"""

import argparse
import json
import os
import re
import urllib.request
from pathlib import Path

from baseline_prompt import build

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data" / "processed" / "baseline_cases.json"
OUTDIR = ROOT / "data" / "processed"


def post(url, payload, headers):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())


def call_ollama(model, system, user):
    r = post(
        "http://localhost:11434/api/chat",
        {"model": model, "stream": False,
         "messages": [{"role": "system", "content": system},
                      {"role": "user", "content": user}],
         "options": {"temperature": 0.7}},
        {"Content-Type": "application/json"},
    )
    return r["message"]["content"]


def call_openai(model, system, user):
    key = os.environ["OPENAI_API_KEY"]
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    r = post(
        f"{base}/chat/completions",
        {"model": model, "temperature": 0.7,
         "messages": [{"role": "system", "content": system},
                      {"role": "user", "content": user}]},
        {"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    return r["choices"][0]["message"]["content"]


def call_anthropic(model, system, user):
    key = os.environ["ANTHROPIC_API_KEY"]
    r = post(
        "https://api.anthropic.com/v1/messages",
        {"model": model, "max_tokens": 400, "temperature": 0.7,
         "system": system, "messages": [{"role": "user", "content": user}]},
        {"Content-Type": "application/json", "x-api-key": key,
         "anthropic-version": "2023-06-01"},
    )
    return r["content"][0]["text"]


# ---- the non-LLM control -------------------------------------------------
# plan.md Section 2: "if the fine-tuned model only marginally beats a dumb
# template on style, that tells you something important about where the value
# actually is." This is that dumb template.
GREEK = {"alpha": "α", "beta": "β", "gamma": "γ",
         "delta": "δ", "epsilon": "ε", "zeta": "ζ",
         "eta": "η", "theta": "ϑ", "mu": "μ", "rho": "ρ"}


def greekify(name):
    parts = name.split()
    if parts and parts[0].lower() in GREEK:
        return GREEK[parts[0].lower()] + " " + " ".join(parts[1:])
    return name


def ordinal(n):
    n = int(n)
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def call_template(_model, _system, user):
    """Fill a fixed sentence frame straight from the state JSON. No model."""
    tail = user[user.rfind("<OBSERVATION_STATE>"):]
    m = re.search(r"Events: (\[.*\])", tail)
    day = re.search(r"(?:night of the|the)\s+(\d{1,2})(?:st|nd|rd|th)", tail, re.I)
    if not m:
        return "(template: no events parsed)"
    ev = json.loads(m.group(1))[0]
    d = f"the {ordinal(day.group(1))}" if day else "the day"
    objs = [greekify(o) for o in ev.get("objects", [])]
    kind = ev.get("event", "")
    if kind == "first_appearance":
        return (f"The {ordinal(day.group(1)) if day else 'day'}, {objs[0]}'s first "
                f"appearance{' in ' + ev['sign'] if ev.get('sign') else ''}; "
                f"rising to sunrise: {ev.get('rising_to_sunrise_deg', 'nn')}°.")
    if kind == "lunar_first_visibility":
        return (f"Month, {d}, sunset to moonset: "
                f"{ev.get('sunset_to_moonset_deg', 'nn')}°; it was bright.")
    rel = ev.get("relation", "near")
    sep = ev.get("separation", "")
    lead = objs[0] if objs[0][0].isupper() and " " not in objs[0] else f"the {objs[0].lower()}"
    return (f"Night of {d}, {lead} was {sep} {rel} {objs[1]}."
            if len(objs) > 1 else f"Night of {d}, {objs[0]} was visible.")


BACKENDS = {"ollama": call_ollama, "openai": call_openai,
            "anthropic": call_anthropic, "template": call_template}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", required=True, choices=list(BACKENDS))
    ap.add_argument("--model", default="template")
    ap.add_argument("--shots", type=int, default=5)
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()

    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    fn = BACKENDS[a.backend]
    tier = "zero-shot" if a.shots == 0 else f"few-shot({a.shots})"
    outputs = {}
    for c in cases:
        system, user = build(c, shots=a.shots)
        print(f"  {c['id']} ...", end="", flush=True)
        try:
            outputs[c["id"]] = fn(a.model, system, user).strip()
            print(" ok")
        except Exception as e:
            outputs[c["id"]] = f"(ERROR: {e})"
            print(f" ERROR {e}")

    tag = a.tag or f"{a.backend}_{a.model.replace(':', '-').replace('/', '-')}_{a.shots}shot"
    out = OUTDIR / f"baseline_run_{tag}.json"
    out.write_text(json.dumps(
        {"model": a.model, "backend": a.backend, "tier": tier, "outputs": outputs},
        indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {out}\nnow: python scripts/score_baseline.py {out}")


if __name__ == "__main__":
    main()
