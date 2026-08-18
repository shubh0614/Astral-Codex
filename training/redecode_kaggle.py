"""
Re-decode the saved adapter. No training.

The 3-epoch 7B run kept the register and lost the facts, and every fact failure
was the model looping or running long rather than getting anything wrong:
repeated clauses, a second invented observation, "medium confidence" bleeding out
of the state, an unfilled x-degrees placeholder. Generation ran at temperature
0.7 with no repetition penalty and max_new_tokens=160, which is seven times the
22-word reference mean. So the first thing to test is the decoder, not another 56
minutes of training.

This loads the adapter that run saved and regenerates the same three files under
four decoder settings, including a reproduction of the original so the comparison
is against a measured number rather than a remembered one.

Kaggle Script, Save and Run All. T4, internet ON. Add the previous run's output
as a data source (Add Data, then Notebook Output); the adapter is found
automatically under /kaggle/input.
"""

import os
import sys
import time
import warnings

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["DATASETS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_VERBOSITY"] = "error"
os.environ["BITSANDBYTES_NOWELCOME"] = "1"
warnings.filterwarnings("ignore")

BASE = "Qwen/Qwen2.5-7B-Instruct"
REPO = "https://raw.githubusercontent.com/shubh0614/Astral-Codex/master"
WORK = "/kaggle/working"
SEED = 20260816

# The reference entries average 22 words. 160 new tokens let the model write four
# more observations after finishing the one it was asked for, which is exactly
# what bab-04 and gen-03 did.
CONFIGS = {
    "orig": dict(do_sample=True, temperature=0.7, max_new_tokens=160,
                 _why="reproduction of the failing run, the control"),
    "greedy": dict(do_sample=False, max_new_tokens=80, repetition_penalty=1.15,
                   no_repeat_ngram_size=6,
                   _why="the recommended setting: no sampling, penalise loops, "
                        "cap length near the reference mean"),
    "sampled": dict(do_sample=True, temperature=0.7, max_new_tokens=80,
                    repetition_penalty=1.15, no_repeat_ngram_size=6,
                    _why="same guards, sampling kept, to separate the effect of "
                         "the penalty from the effect of greedy decoding"),
    "greedy_firstline": dict(do_sample=False, max_new_tokens=80,
                             repetition_penalty=1.15, no_repeat_ngram_size=6,
                             _first_line=True,
                             _why="greedy, then keep only the first line. A diary "
                                  "entry is one dated unit, so anything after the "
                                  "first newline is a second entry the state did "
                                  "not ask for"),
}

_T0 = time.time()


def log(msg=""):
    print(f"[{time.time()-_T0:7.1f}s] {msg}", flush=True)


def section(title):
    bar = "=" * 62
    print(flush=True)
    print(f"[{time.time()-_T0:7.1f}s] {bar}", flush=True)
    print(f"[{time.time()-_T0:7.1f}s] {title}", flush=True)
    print(f"[{time.time()-_T0:7.1f}s] {bar}", flush=True)


section("Astral Codex, re-decode of the saved adapter")
for name, cfg in CONFIGS.items():
    log(f"{name:18s} {cfg['_why']}")

import json
import urllib.request

import torch
from peft import PeftModel
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          BitsAndBytesConfig)

section("locate adapter")


def find_adapter():
    """Prefer a mounted previous-run output, fall back to this session's dir."""
    found = []
    for root in ("/kaggle/input", WORK):
        if not os.path.isdir(root):
            continue
        for dirpath, _, files in os.walk(root):
            if "adapter_config.json" in files:
                found.append(dirpath)
    return found


cands = find_adapter()
for c in cands:
    log(f"candidate {c}")
if not cands:
    log("no adapter_config.json anywhere under /kaggle/input or /kaggle/working.")
    log("Add the training run's output: Add Data, Notebook Output, then rerun.")
    sys.exit(1)
ADAPTER = cands[0]
log(f"using {ADAPTER}")

section("model")
tok = AutoTokenizer.from_pretrained(BASE)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

bnb = BitsAndBytesConfig(
    load_in_4bit=True, bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)
log("loading base in 4-bit nf4")
try:
    model = AutoModelForCausalLM.from_pretrained(
        BASE, quantization_config=bnb, device_map={"": 0}, dtype=torch.float16)
except TypeError:
    model = AutoModelForCausalLM.from_pretrained(
        BASE, quantization_config=bnb, device_map={"": 0},
        torch_dtype=torch.float16)
log("attaching adapter")
model = PeftModel.from_pretrained(model, ADAPTER)
model.eval()
model.config.use_cache = True
log("ready")

section("data")
os.makedirs(f"{WORK}/data", exist_ok=True)
for name in ("train.jsonl", "test.jsonl",
             "baseline_cases.json", "baseline_cases_generalization.json"):
    dest = f"{WORK}/data/{name}"
    urllib.request.urlretrieve(f"{REPO}/data/processed/{name}", dest)
    log(f"fetched {name}")

with open(f"{WORK}/data/train.jsonl", encoding="utf-8") as f:
    SYSTEM = json.loads(f.readline())["messages"][0]["content"]
with open(f"{WORK}/data/test.jsonl", encoding="utf-8") as f:
    test_rows = [json.loads(line) for line in f if line.strip()][:25]
log(f"system prompt {len(SYSTEM)} chars, {len(test_rows)} test pairs")


def generate(state, cfg):
    kw = {k: v for k, v in cfg.items() if not k.startswith("_")}
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": state}]
    prompt = tok.apply_chat_template(msgs, tokenize=False,
                                     add_generation_prompt=True)
    ids = tok(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**ids, pad_token_id=tok.pad_token_id,
                             eos_token_id=tok.eos_token_id, **kw)
    text = tok.decode(out[0][ids["input_ids"].shape[1]:],
                      skip_special_tokens=True).strip()
    if cfg.get("_first_line"):
        text = text.split("\n")[0].strip()
    return text


written = []

for cname, cfg in CONFIGS.items():
    section(f"decode: {cname}")
    torch.manual_seed(SEED)
    for fname, tag in (("baseline_cases", "main"),
                       ("baseline_cases_generalization", "gen")):
        with open(f"{WORK}/data/{fname}.json", encoding="utf-8") as f:
            cases = json.load(f)["cases"]
        outputs = {}
        for c in cases:
            outputs[c["id"]] = generate(c["observation_state"], cfg)
            log(f"  {c['id']:14s} {outputs[c['id']][:130]}")
        payload = {"model": BASE, "backend": "qlora",
                   "tier": f"finetuned(3ep) decode={cname}",
                   "decode": {k: v for k, v in cfg.items() if k != "_why"},
                   "cases_file": f"data/processed/{fname}.json",
                   "outputs": outputs}
        path = f"{WORK}/redecode_{tag}_{cname}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        written.append(os.path.basename(path))
        log(f"wrote {os.path.basename(path)}")

    sample = []
    for r in test_rows:
        sample.append({"state": r["messages"][1]["content"],
                       "reference": r["messages"][2]["content"],
                       "generated": generate(r["messages"][1]["content"], cfg),
                       "meta": r["meta"]})
    rl = sum(len(s["reference"].split()) for s in sample) / len(sample)
    gl = sum(len(s["generated"].split()) for s in sample) / len(sample)
    log(f"  mean words: reference {rl:.1f}, generated {gl:.1f}, ratio {gl/rl:.2f}")
    path = f"{WORK}/redecode_sample_{cname}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sample, f, indent=2, ensure_ascii=False)
    written.append(os.path.basename(path))
    log(f"wrote {os.path.basename(path)}  ({len(sample)} pairs)")

section("done")
log(f"total {(time.time()-_T0)/60:.1f} min")
log(f"{len(written)} files written, {len(CONFIGS)} configs x 3 files each. "
    f"Anything missing below means that config errored, scroll up for it.")
for name in written:
    log(f"  {name}")

log()
log("download all of them, put them in data/processed/, then score every config,")
log("not just the promising one. orig should reproduce 3/5; if it does not, the")
log("comparison is unstable and nothing else in this run means anything.")
for cname in CONFIGS:
    log(f"  python scripts/score_baseline.py data/processed/redecode_main_{cname}.json")
    log(f"  python scripts/score_baseline.py data/processed/redecode_gen_{cname}.json")
    log(f"  python scripts/score_register.py data/processed/redecode_sample_{cname}.json")
log()
log("bar: few-shot at 5/5 main and 4/4 gen, with the zero modern drift the 3ep run had")
