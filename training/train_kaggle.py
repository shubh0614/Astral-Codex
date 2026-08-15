"""
QLoRA fine-tune for the Babylonian observation genre.

Kaggle Script, run with Save and Run All. Writes a linear, readable log: no
progress bars, no library warnings, one line per meaningful event.

Accelerator: T4 or T4 x2, NOT P100. bitsandbytes 4-bit is unreliable on Pascal
(compute 6.0); T4 is 7.5. Neither has bf16, so fp16 throughout.
Settings: internet must be ON, the script pulls its data from GitHub.

Set SMOKE below. True runs 1.5B for one epoch to prove the pipeline. False runs
Qwen2.5-7B-Instruct, which is the run that gets compared against the few-shot
baseline (7B because the baseline was 7B; a fine-tuned 1.5B against a few-shot
7B would measure model size, not fine-tuning).
"""

import os
import sys
import time
import warnings

# Must happen before torch or transformers are imported or these are ignored.
#
# Only expose one GPU. On a T4 x2 instance the HF Trainer sees two devices and
# silently wraps the model in nn.DataParallel, which replicates it onto cuda:1
# while the 4-bit weights are pinned to cuda:0, and every step dies with
# "Expected all tensors to be on the same device". DataParallel is deprecated
# and poor with quantized models anyway, and a 7B in 4-bit is about 5 GB, so one
# 15.6 GB T4 is plenty.
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["DATASETS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_VERBOSITY"] = "error"
os.environ["BITSANDBYTES_NOWELCOME"] = "1"
warnings.filterwarnings("ignore")

SMOKE = True
REPO = "https://raw.githubusercontent.com/shubh0614/Astral-Codex/master"
MODEL = "Qwen/Qwen2.5-1.5B-Instruct" if SMOKE else "Qwen/Qwen2.5-7B-Instruct"
EPOCHS = 1 if SMOKE else 3
LORA_R, LORA_ALPHA, LORA_DROPOUT = 16, 32, 0.05
LR = 2e-4
MAX_SEQ = 1024
SEED = 20260816
WORK = "/kaggle/working"
OUT = f"{WORK}/adapter"
INSTALL = True

_T0 = time.time()


def log(msg=""):
    print(f"[{time.time()-_T0:7.1f}s] {msg}", flush=True)


def section(title):
    print(flush=True)
    print(f"[{time.time()-_T0:7.1f}s] {'=' * 62}", flush=True)
    print(f"[{time.time()-_T0:7.1f}s] {title}", flush=True)
    print(f"[{time.time()-_T0:7.1f}s] {'=' * 62}", flush=True)


def pip_install():
    """Install only what is missing, and do NOT pass -U.

    Forcing an upgrade pulled transformers 5.15 and trl 1.10 onto the image,
    which is how the first two runs broke: the config signature had moved and
    TRL's chunked-CE patch was incompatible with accelerate's forward wrapper.
    Kaggle's preinstalled versions are a tested combination; leave them alone.
    """
    import importlib
    import subprocess
    def missing(mod):
        try:
            return importlib.util.find_spec(mod) is None
        except (ImportError, ValueError):
            return True

    need = [p for p in ("transformers", "peft", "trl", "bitsandbytes",
                        "accelerate", "datasets") if missing(p)]
    if not need:
        log("all packages already present, installing nothing")
        return
    log(f"installing missing: {', '.join(need)}")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", *need],
                       capture_output=True, text=True)
    if r.returncode != 0:
        log("pip FAILED")
        print(r.stdout[-3000:], r.stderr[-3000:], flush=True)
        sys.exit(1)
    log("install ok")


section("Astral Codex, Babylonian QLoRA")
log(f"mode        : {'SMOKE (pipeline check, not a result)' if SMOKE else 'REAL'}")
log(f"model       : {MODEL}")
log(f"epochs      : {EPOCHS}")
log(f"lora        : r={LORA_R} alpha={LORA_ALPHA} dropout={LORA_DROPOUT}")
log(f"lr          : {LR}")
log(f"max_seq     : {MAX_SEQ}")

if INSTALL:
    pip_install()

import json
import inspect
import urllib.request

import torch
import transformers
import trl
from datasets import Dataset
from peft import LoraConfig
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          BitsAndBytesConfig, TrainerCallback)
from trl import SFTConfig, SFTTrainer

transformers.logging.set_verbosity_error()

section("environment")
log(f"torch        {torch.__version__}")
log(f"transformers {transformers.__version__}")
log(f"trl          {trl.__version__}")
if torch.cuda.is_available():
    log(f"visible gpus {torch.cuda.device_count()} "
        f"(pinned to one on purpose, see CUDA_VISIBLE_DEVICES at the top)")
    for i in range(torch.cuda.device_count()):
        p = torch.cuda.get_device_properties(i)
        log(f"gpu {i}        {p.name}, {p.total_memory/1e9:.1f} GB, "
            f"compute {p.major}.{p.minor}")
        if p.major < 7:
            log("WARNING: compute < 7.0, bitsandbytes 4-bit is unreliable here. "
                "Switch the accelerator to T4.")
else:
    log("no GPU visible, stopping")
    sys.exit(1)

section("data")
os.makedirs(f"{WORK}/data", exist_ok=True)
for name in ("train.jsonl", "val.jsonl", "test.jsonl",
             "baseline_cases.json", "baseline_cases_generalization.json"):
    dest = f"{WORK}/data/{name}"
    urllib.request.urlretrieve(f"{REPO}/data/processed/{name}", dest)
    log(f"fetched {name:38s} {os.path.getsize(dest):>9,} bytes")


def load_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


train_rows = load_jsonl(f"{WORK}/data/train.jsonl")
val_rows = load_jsonl(f"{WORK}/data/val.jsonl")
test_rows = load_jsonl(f"{WORK}/data/test.jsonl")
log(f"train {len(train_rows)}   val {len(val_rows)}   test {len(test_rows)}")

import collections
mix = collections.Counter(r["meta"]["class"] for r in train_rows)
log("train class mix: " + ", ".join(f"{k}={v}" for k, v in mix.most_common()))
tgt_chars = sum(len(r["messages"][2]["content"]) for r in train_rows)
log(f"approx target tokens: {tgt_chars//4:,}  (small, watch eval loss)")

section("model")
log("loading tokenizer")
tok = AutoTokenizer.from_pretrained(MODEL)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

log("loading model in 4-bit nf4")
bnb = BitsAndBytesConfig(
    load_in_4bit=True, bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)

# Pin to one GPU rather than device_map="auto". A 7B in 4-bit is about 5 GB and
# fits a single 15.6 GB T4 comfortably, splitting it across two only adds
# cross-device traffic. It also avoids accelerate wrapping model.forward in a
# functools.partial, which TRL's chunked cross-entropy patch cannot handle.
DEVICE_MAP = {"": 0}
try:
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, quantization_config=bnb, device_map=DEVICE_MAP, dtype=torch.float16)
except TypeError:
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, quantization_config=bnb, device_map=DEVICE_MAP,
        torch_dtype=torch.float16)
model.config.use_cache = False
log(f"loaded, {sum(p.numel() for p in model.parameters())/1e9:.2f} B params")

# Standard QLoRA preparation: casts layernorms and other small non-quantized
# modules to fp32 and wires up gradient checkpointing. Without it some trainable
# params stay bf16, and fp16's GradScaler cannot unscale bf16 gradients:
#   NotImplementedError: _amp_foreach_non_finite_check_and_unscale_cuda
#   not implemented for 'BFloat16'
# The T4 has no bf16 support at all, so fp32 trainable params is the right shape
# here regardless.
from peft import prepare_model_for_kbit_training

model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
dtypes = {}
for _, p in model.named_parameters():
    dtypes[str(p.dtype)] = dtypes.get(str(p.dtype), 0) + p.numel()
log("param dtypes: " + ", ".join(f"{k}={v/1e6:.1f}M" for k, v in dtypes.items()))

import functools


def disable_chunked_ce(reason):
    """TRL 1.10's chunked cross-entropy patch does
    inspect.signature(model.forward.__func__), which assumes forward is a bound
    method. Accelerate's device hooks replace it with a functools.partial and the
    patch dies. It is a memory optimisation, not required for correctness, so it
    gets switched off."""
    import trl.trainer.sft_trainer as sft
    if hasattr(sft, "_patch_chunked_ce_lm_head"):
        sft._patch_chunked_ce_lm_head = lambda *a, **k: None
        log(f"disabled TRL chunked-CE patch ({reason})")
        return True
    return False


if isinstance(getattr(model, "forward", None), functools.partial):
    disable_chunked_ce("model.forward is a functools.partial")


def to_text(row):
    return {"text": tok.apply_chat_template(row["messages"], tokenize=False)}


ds_train = Dataset.from_list(train_rows).map(
    to_text, remove_columns=["messages", "meta"])
ds_val = Dataset.from_list(val_rows).map(
    to_text, remove_columns=["messages", "meta"])
log(f"formatted, example is {len(ds_train[0]['text'])} chars")

section("trainer config")
# TRL's signature moves between releases, so ask the installed classes what they
# accept instead of pinning a version that will go stale on the Kaggle image.
WANTED = {
    "output_dir": OUT, "num_train_epochs": EPOCHS,
    "per_device_train_batch_size": 2, "per_device_eval_batch_size": 2,
    "gradient_accumulation_steps": 8, "learning_rate": LR,
    "lr_scheduler_type": "cosine", "warmup_ratio": 0.05,
    "logging_steps": 5, "eval_strategy": "steps", "evaluation_strategy": "steps",
    "eval_steps": 25, "save_strategy": "steps", "save_steps": 25,
    "save_total_limit": 2, "load_best_model_at_end": True,
    "metric_for_best_model": "eval_loss", "greater_is_better": False,
    "fp16": True, "max_length": MAX_SEQ, "max_seq_length": MAX_SEQ,
    "gradient_checkpointing": True, "report_to": "none", "seed": SEED,
    "disable_tqdm": True, "logging_strategy": "steps",
}


def supported(cls, wanted):
    # No **kwargs shortcut: a class can accept kwargs and still reject the key
    # downstream, which is how the first attempt at this failed.
    ok = set(inspect.signature(cls.__init__).parameters)
    for base in getattr(cls, "__mro__", []):
        try:
            ok |= set(inspect.signature(base.__init__).parameters)
        except (TypeError, ValueError):
            pass
    keep = {k: v for k, v in wanted.items() if k in ok}
    dropped = sorted(set(wanted) - set(keep))
    if dropped:
        log(f"{cls.__name__} does not accept: {', '.join(dropped)}")
    return keep


cfg = supported(SFTConfig, WANTED)
for new, old in (("eval_strategy", "evaluation_strategy"),
                 ("max_length", "max_seq_length")):
    if new in cfg and old in cfg:
        cfg.pop(old)
if not ({"eval_strategy", "evaluation_strategy"} & set(cfg)):
    log("no eval strategy accepted, disabling best-model selection")
    for k in ("load_best_model_at_end", "metric_for_best_model",
              "greater_is_better", "eval_steps"):
        cfg.pop(k, None)
log("passing: " + ", ".join(sorted(cfg)))
args = SFTConfig(**cfg)

peft_cfg = LoraConfig(
    r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=LORA_DROPOUT,
    bias="none", task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"])


class Progress(TrainerCallback):
    """One clean line per logged step. tqdm bars are unreadable in a job log."""

    def on_log(self, args, state, control, logs=None, **kw):
        if not logs:
            return
        if "loss" in logs:
            log(f"step {state.global_step:4d}/{state.max_steps}  "
                f"loss {logs['loss']:.4f}  lr {logs.get('learning_rate', 0):.2e}"
                f"  epoch {logs.get('epoch', 0):.2f}")
        if "eval_loss" in logs:
            log(f"step {state.global_step:4d}  EVAL loss {logs['eval_loss']:.4f}")


section("training")
tk = supported(SFTTrainer, {
    "model": model, "args": args, "train_dataset": ds_train,
    "eval_dataset": ds_val, "peft_config": peft_cfg,
    "processing_class": tok, "tokenizer": tok, "callbacks": [Progress()]})
if "processing_class" in tk:
    tk.pop("tokenizer", None)
try:
    trainer = SFTTrainer(**tk)
except AttributeError as e:
    if "__func__" not in str(e):
        raise
    if not disable_chunked_ce(f"constructor raised {e}"):
        raise
    trainer = SFTTrainer(**tk)

# Belt and braces: whatever PEFT built inside the trainer, no trainable param may
# be bf16 or the fp16 GradScaler dies on the first clip_grad_norm_.
recast = 0
for _, p in trainer.model.named_parameters():
    if p.requires_grad and p.dtype == torch.bfloat16:
        p.data = p.data.float()
        recast += 1
tr = [p for p in trainer.model.parameters() if p.requires_grad]
log(f"trainable tensors {len(tr)}, "
    f"{sum(p.numel() for p in tr)/1e6:.2f}M params, "
    f"dtypes {sorted({str(p.dtype) for p in tr})}")
if recast:
    log(f"recast {recast} bf16 trainable tensors to fp32")

t_train = time.time()
trainer.train()
log(f"training finished in {(time.time()-t_train)/60:.1f} min")
trainer.save_model(OUT)
log(f"adapter saved to {OUT}")

section("loss curve")
evals = [(h["step"], h["eval_loss"])
         for h in trainer.state.log_history if "eval_loss" in h]
if evals:
    for step, loss in evals:
        log(f"  step {step:4d}   eval_loss {loss:.4f}")
    best = min(evals, key=lambda x: x[1])
    log(f"best eval_loss {best[1]:.4f} at step {best[0]}")
    if evals[-1][1] > best[1] * 1.05:
        log("eval loss rose after its minimum: overfitting. "
            "Use fewer epochs or drop LORA_R to 8.")
    else:
        log("eval loss did not turn upward, no obvious overfitting")
else:
    log("no eval records, evaluation did not run")

section("generation")
model.config.use_cache = True
model.eval()
SYSTEM = train_rows[0]["messages"][0]["content"]


def generate(state, max_new_tokens=160):
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": state}]
    prompt = tok.apply_chat_template(msgs, tokenize=False,
                                     add_generation_prompt=True)
    ids = tok(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**ids, max_new_tokens=max_new_tokens,
                             temperature=0.7, do_sample=True,
                             pad_token_id=tok.pad_token_id)
    return tok.decode(out[0][ids["input_ids"].shape[1]:],
                      skip_special_tokens=True).strip()


for name, tag in (("baseline_cases", "main"),
                  ("baseline_cases_generalization", "gen")):
    with open(f"{WORK}/data/{name}.json", encoding="utf-8") as f:
        cases = json.load(f)["cases"]
    log(f"--- {tag}: {len(cases)} cases ---")
    outputs = {}
    for c in cases:
        outputs[c["id"]] = generate(c["observation_state"])
        log(f"  {c['id']}")
        log(f"    {outputs[c['id']][:160]}")
    payload = {
        "model": MODEL, "backend": "qlora", "tier": f"finetuned({EPOCHS}ep)",
        "cases_file": f"data/processed/{name}.json", "outputs": outputs}
    with open(f"{WORK}/finetune_{tag}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    log(f"wrote finetune_{tag}.json")

log("--- held-out test sample, for reading register by hand ---")
sample = []
for r in test_rows[:25]:
    gen = generate(r["messages"][1]["content"])
    sample.append({"state": r["messages"][1]["content"],
                   "reference": r["messages"][2]["content"],
                   "generated": gen, "meta": r["meta"]})
for s in sample[:5]:
    log(f"  REF : {s['reference'][:150]}")
    log(f"  GEN : {s['generated'][:150]}")
    log("")
with open(f"{WORK}/finetune_test_sample.json", "w", encoding="utf-8") as f:
    json.dump(sample, f, indent=2, ensure_ascii=False)
log(f"wrote finetune_test_sample.json  ({len(sample)} pairs)")

section("done")
log(f"total {(time.time()-_T0)/60:.1f} min")
log("download finetune_main.json, finetune_gen.json, finetune_test_sample.json")
log("score locally: python scripts/score_baseline.py data/processed/finetune_main.json")
log("bar to beat: qwen2.5:7b few-shot at 5/5 main and 4/4 gen")
