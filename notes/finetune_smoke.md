# Smoke run, Qwen2.5-1.5B, 1 epoch (2026-08-16)

**Not a result.** The smoke run exists to prove the pipeline. It did that, and it
also surfaced two things worth acting on before the 7B run.

Five earlier attempts failed before training started: TRL config signature,
TRL chunked-CE against accelerate's forward wrapper, DataParallel across two
T4s, and bf16 trainable params against the fp16 GradScaler. All fixed, all
documented in `training/README.md`. Total cost about ninety seconds each rather
than two hours of quota.

## The run

| | |
|---|---|
| model | Qwen2.5-1.5B-Instruct, QLoRA nf4, r=16 |
| data | 933 train, 97 val, 124 test |
| steps | 59, one epoch, 5.9 min |
| trainable | 18.46M params, all fp32 after recasting 392 bf16 tensors |
| train loss | 3.29 to 0.19 |
| eval loss | 0.2690 at step 25, **0.2072** at step 50 |
| overfitting | none visible at one epoch |

## Scores

| | main | held-out |
|---|---|---|
| template control | 0/5 | 0/4 |
| qwen2.5:7b zero-shot | 0/5 | - |
| qwen2.5:7b few-shot | 5/5 | 4/4 |
| **1.5B fine-tuned, 1 epoch** | **2/5** | **0/4** |

## What the failures actually say

Outcome tracks the training count almost perfectly:

| case | class | train examples | outcome |
|---|---|---:|---|
| bab-01 moon-star | conjunction | 319 | PASS |
| bab-03 planet-planet | conjunction | 319 | PASS |
| bab-02 moon-planet | conjunction | 319 | FAIL, relation reversed |
| lunar first visibility | lunar_six | 169 | FAIL |
| gen-02 last appearance | last_appearance | 119 | FAIL |
| bab-04 heliacal | first_appearance | 110 | FAIL |
| gen-03 eclipse | eclipse | 41 | FAIL |
| gen-01 stationary | stationary_point | 14 | FAIL |
| gen-04 acronychal | acronychal_rising | 10 | FAIL |

**Only the 319-example class passed.** That is a data problem, not a capacity
problem, so going to 7B will improve it but will not solve it. Ten acronychal
examples remain ten acronychal examples.

The relation reversal on bab-02 is worth noting on its own: the model wrote
"Jupiter was behind the Moon" for a state saying the Moon was behind Jupiter.
Criterion (f) caught it. That is the failure plan.md Section 2 predicted a regex
validator could not catch, and the reason (f) exists.

## Two behaviours to watch at 7B

**State syntax leaking into the output.** gen-02 ended with "confidence: medium",
copied straight out of the OBSERVATION_STATE format rather than written as prose.

**A learned tic.** "I did not watch" appears in outputs where nothing in the
state warrants it. It is frequent in the training text and the model has latched
onto it. Classic small-corpus behaviour, and something to check specifically at
3 epochs where it may get worse.

## The bug this run exposed

Training states used Greek letters (`δ Capricorni`) while both the evaluation
cases and `engine/sky.py` use spelled-out names (`delta Capricorni`,
`eta Piscium`). 1382 of 2724 states were affected. The model was being trained in
one format and queried in another.

This is exactly the drift the training-set card flagged: "training states are
derived from diary text, at inference they will come from the engine, if the two
formats drift the model breaks exactly when you start using it." It did.

Fixed: the state now spells star names out, matching the engine and the eval
cases, while the entry keeps the Greek letter because that is what the diaries
print. The model learns spelled-out state to Greek entry, which is the mapping
actually wanted at inference. Zero states now contain Greek.

## What to expect from the 7B run

Conjunctions should hold. The rare classes will likely still fail, because the
constraint is example count rather than model size. If the 7B lands well below
few-shot's 5/5 and 4/4, the honest read is that this corpus does not support
fine-tuning for rare phenomena, and the sensible architecture is few-shot
prompting for those with the fine-tune covering the common cases, or simply
prompting throughout.
