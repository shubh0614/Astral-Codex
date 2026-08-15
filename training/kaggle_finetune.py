"""
QLoRA fine-tune for the Babylonian observation genre. Written to be pasted into
a Kaggle notebook one cell at a time (the # %% markers are the cell breaks).

Accelerator: pick T4 x2 or a single T4, NOT P100. bitsandbytes 4-bit is
unreliable on Pascal (compute 6.0); T4 is 7.5 and fully supported. Neither
card has bf16, so everything below uses fp16.

Two runs are intended:
  SMOKE   Qwen2.5-1.5B-Instruct, 1 epoch, catches data-loader and format bugs
          for a few minutes of quota instead of two hours
  REAL    Qwen2.5-7B-Instruct, the run that gets compared against the few-shot
          baseline. 7B because the baseline was 7B; comparing a fine-tuned 1.5B
          against a few-shot 7B would measure model size, not fine-tuning.

The notebook trains, then generates on the held-out test split and on the 9
quarantined evaluation cases, and writes the outputs to /kaggle/working. Scoring
happens locally with scripts/score_baseline.py, which is CPU-only.
"""

# %% [cell 1] install
# !pip install -q -U transformers peft trl bitsandbytes accelerate datasets

# %% [cell 2] config
import json
import os
import urllib.request

SMOKE = True          # set False for the real 7B run
REPO = "https://raw.githubusercontent.com/shubh0614/Astral-Codex/master"

MODEL = "Qwen/Qwen2.5-1.5B-Instruct" if SMOKE else "Qwen/Qwen2.5-7B-Instruct"
EPOCHS = 1 if SMOKE else 3
OUT = "/kaggle/working/adapter"

# Small corpus, around 25k target tokens. Rank stays modest on purpose:
# plan.md warns about overfitting and this is exactly the size where it bites.
LORA_R, LORA_ALPHA, LORA_DROPOUT = 16, 32, 0.05
LR = 2e-4
MAX_SEQ = 1024

# %% [cell 3] data
os.makedirs("/kaggle/working/data", exist_ok=True)
for name in ("train", "val", "test"):
    urllib.request.urlretrieve(
        f"{REPO}/data/processed/{name}.jsonl", f"/kaggle/working/data/{name}.jsonl")

for name in ("baseline_cases", "baseline_cases_generalization"):
    urllib.request.urlretrieve(
        f"{REPO}/data/processed/{name}.json", f"/kaggle/working/data/{name}.json")


def load_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


train_rows = load_jsonl("/kaggle/working/data/train.jsonl")
val_rows = load_jsonl("/kaggle/working/data/val.jsonl")
test_rows = load_jsonl("/kaggle/working/data/test.jsonl")
print(f"train {len(train_rows)}  val {len(val_rows)}  test {len(test_rows)}")
print(train_rows[0]["messages"][1]["content"][:300])

# %% [cell 4] model
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
)
tok = AutoTokenizer.from_pretrained(MODEL)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

try:
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, quantization_config=bnb, device_map="auto", dtype=torch.float16)
except TypeError:
    # older transformers still wants torch_dtype
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, quantization_config=bnb, device_map="auto",
        torch_dtype=torch.float16)
model.config.use_cache = False

# %% [cell 5] dataset
from datasets import Dataset


def to_text(row):
    return {"text": tok.apply_chat_template(row["messages"], tokenize=False)}


ds_train = Dataset.from_list(train_rows).map(to_text, remove_columns=["messages", "meta"])
ds_val = Dataset.from_list(val_rows).map(to_text, remove_columns=["messages", "meta"])
print(ds_train[0]["text"][:400])

# %% [cell 6] train
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

peft_cfg = LoraConfig(
    r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=LORA_DROPOUT,
    bias="none", task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
)

import inspect
import trl

# TRL's SFTConfig signature moves between releases: warmup_ratio, max_length vs
# max_seq_length and eval_strategy vs evaluation_strategy have all shifted.
# Rather than pin a version that will go stale, ask the installed class what it
# accepts and drop the rest, printing whatever got dropped.
print("trl", trl.__version__)

WANTED = {
    "output_dir": OUT,
    "num_train_epochs": EPOCHS,
    "per_device_train_batch_size": 2,
    "per_device_eval_batch_size": 2,
    "gradient_accumulation_steps": 8,
    "learning_rate": LR,
    "lr_scheduler_type": "cosine",
    "warmup_ratio": 0.05,
    "logging_steps": 10,
    "eval_strategy": "steps",
    "evaluation_strategy": "steps",
    "eval_steps": 25,
    "save_strategy": "steps",
    "save_steps": 25,
    "save_total_limit": 2,
    "load_best_model_at_end": True,
    "metric_for_best_model": "eval_loss",
    "greater_is_better": False,
    "fp16": True,
    "max_length": MAX_SEQ,
    "max_seq_length": MAX_SEQ,
    "gradient_checkpointing": True,
    "report_to": "none",
    "seed": 20260816,
}


def supported(cls, wanted):
    ok = set(inspect.signature(cls.__init__).parameters)
    for base in getattr(cls, "__mro__", []):
        try:
            ok |= set(inspect.signature(base.__init__).parameters)
        except (TypeError, ValueError):
            pass
    # Deliberately no **kwargs shortcut. A class can accept **kwargs and still
    # reject the key downstream, which is exactly how the first run failed.
    keep = {k: v for k, v in wanted.items() if k in ok}
    dropped = sorted(set(wanted) - set(keep))
    if dropped:
        print(f"{cls.__name__}: dropped, not supported here: {dropped}")
    return keep


cfg = supported(SFTConfig, WANTED)
# only one of each aliased pair should survive; prefer the modern name
for new, old in (("eval_strategy", "evaluation_strategy"),
                 ("max_length", "max_seq_length")):
    if new in cfg and old in cfg:
        cfg.pop(old)

# load_best_model_at_end needs an eval strategy; if neither alias survived,
# evaluation never runs and the trainer would error on the mismatch
if not ({"eval_strategy", "evaluation_strategy"} & set(cfg)):
    print("no eval strategy accepted, disabling best-model selection")
    for k in ("load_best_model_at_end", "metric_for_best_model",
              "greater_is_better", "eval_steps"):
        cfg.pop(k, None)

print("passing to SFTConfig:", sorted(cfg))
args = SFTConfig(**cfg)

trainer_kwargs = supported(SFTTrainer, {
    "model": model, "args": args, "train_dataset": ds_train,
    "eval_dataset": ds_val, "peft_config": peft_cfg,
    "processing_class": tok, "tokenizer": tok,
})
if "processing_class" in trainer_kwargs:
    trainer_kwargs.pop("tokenizer", None)
trainer = SFTTrainer(**trainer_kwargs)
trainer.train()
trainer.save_model(OUT)
print("saved to", OUT)

# %% [cell 7] watch this
# Validation loss is the thing to read, not training loss. With ~25k target
# tokens, train loss falling while eval loss rises means it has memorised the
# corpus. If that happens: fewer epochs, or drop LORA_R to 8.
hist = [h for h in trainer.state.log_history if "eval_loss" in h]
for h in hist:
    print(f"step {h['step']:5d}  eval_loss {h['eval_loss']:.4f}")

# %% [cell 8] generate for scoring
model.config.use_cache = True
model.eval()

SYSTEM = train_rows[0]["messages"][0]["content"]


def generate(state, max_new_tokens=160):
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": state}]
    prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    ids = tok(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**ids, max_new_tokens=max_new_tokens,
                             temperature=0.7, do_sample=True,
                             pad_token_id=tok.pad_token_id)
    return tok.decode(out[0][ids["input_ids"].shape[1]:],
                      skip_special_tokens=True).strip()


results = {}
for name in ("baseline_cases", "baseline_cases_generalization"):
    cases = json.load(open(f"/kaggle/working/data/{name}.json", encoding="utf-8"))["cases"]
    outputs = {c["id"]: generate(c["observation_state"]) for c in cases}
    tag = "main" if name == "baseline_cases" else "gen"
    results[tag] = {
        "model": MODEL, "backend": "qlora", "tier": f"finetuned({EPOCHS}ep)",
        "cases_file": ("data/processed/baseline_cases.json" if tag == "main"
                       else "data/processed/baseline_cases_generalization.json"),
        "outputs": outputs,
    }
    for k, v in outputs.items():
        print(f"[{k}] {v[:150]}")
    print()

# held-out test split, for a loss-independent read on register
sample = test_rows[:25]
results["test_sample"] = [
    {"state": r["messages"][1]["content"], "reference": r["messages"][2]["content"],
     "generated": generate(r["messages"][1]["content"]), "meta": r["meta"]}
    for r in sample
]

for tag, payload in results.items():
    p = f"/kaggle/working/finetune_{tag}.json"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print("wrote", p)

# %% [cell 9] download
# From the Kaggle file browser take:
#   finetune_main.json, finetune_gen.json, finetune_test_sample.json
#   adapter/  (the LoRA weights, only worth keeping if the scores are good)
# Then locally:
#   python scripts/score_baseline.py data/processed/finetune_main.json
#   python scripts/score_baseline.py data/processed/finetune_gen.json
# The bar to beat is qwen2.5:7b few-shot at 5/5 and 4/4.
