# Running the fine-tune on Kaggle

Everything is in `kaggle_finetune.py`. The `# %%` markers are cell breaks, so it
pastes into a Kaggle notebook cell by cell.

## Before you start

**Pick T4 x2 or a single T4 as the accelerator, not P100.** bitsandbytes 4-bit
is unreliable on Pascal (the P100 is compute 6.0); the T4 is 7.5 and fully
supported. Neither card has bf16, which is why the config uses fp16 throughout.

Turn the internet toggle ON in the notebook settings. Cell 3 pulls the data
straight from the public GitHub repo, so there is no dataset to upload.

## Run 1: the smoke test

Leave `SMOKE = True`. That uses Qwen2.5-1.5B-Instruct for one epoch and takes a
few minutes.

**It is not a result.** Its only job is to prove the data loads, the chat
template applies, the trainer steps, and the generation cell produces text. Bugs
in any of those cost minutes here instead of two hours on the real run, which is
the whole point of plan.md's model-size ladder.

If it completes and cell 8 prints something that looks like a diary entry, move on.

### If a cell fails on a library signature

The first smoke run died with
`SFTConfig.__init__() got an unexpected keyword argument 'warmup_ratio'`,
because TRL's config signature has moved between releases (`warmup_ratio`,
`max_length` vs `max_seq_length`, `eval_strategy` vs `evaluation_strategy` have
all shifted, and so has `tokenizer` vs `processing_class` on the trainer).

Cell 6 now asks the installed classes what they accept and drops the rest,
printing the TRL version and both the dropped and the passed keys. If it fails
again, that printout says exactly which argument the installed version wants,
which is faster than guessing at a pin.

Nothing is version-pinned on purpose. Pins go stale on Kaggle images.

## Run 2: the real one

Set `SMOKE = False`, restart the session, run again. That gives
Qwen2.5-7B-Instruct for 3 epochs.

**7B specifically, because the baseline was 7B.** qwen2.5:7b with few-shot
prompting already scores 5/5 on the main cases and 4/4 on the held-out ones.
Comparing a fine-tuned 1.5B against that would measure model size, not
fine-tuning. To answer "does fine-tuning beat prompting", the model has to be
held constant.

Expected wall time is well under the 2 hour cap: 933 examples at an effective
batch of 16 is about 58 steps per epoch, so roughly 175 steps total.

## What to actually watch

**Cell 7, validation loss.** Not training loss.

The training set is around 25,000 target tokens. That is small enough that
memorisation is the realistic failure, not undercapacity. If train loss keeps
falling while eval loss turns upward, it has memorised the corpus. Fix by
cutting epochs to 2, or dropping `LORA_R` to 8. Do not raise the rank.

## Getting the results back

From the Kaggle file browser download:

- `finetune_main.json`
- `finetune_gen.json`
- `finetune_test_sample.json`
- `adapter/`, the LoRA weights, only worth keeping if the scores justify it

Put the three JSON files in `data/processed/` locally, then:

```
python scripts/score_baseline.py data/processed/finetune_main.json
python scripts/score_baseline.py data/processed/finetune_gen.json
```

The scorer applies the same six criteria used on every other tier, and it has
been self-tested (`python scripts/selftest_scorer.py`) so its verdicts mean
something.

## The bar

| tier | main set | held-out set |
|---|---|---|
| non-LLM template control | 0/5 | 0/4 |
| qwen2.5:7b zero-shot | 0/5 | - |
| qwen2.5:7b few-shot (5) | 5/5 | 4/4 |
| **qwen2.5:7b fine-tuned** | **?** | **?** |

Matching 5/5 and 4/4 is not a win on its own, because few-shot already does
that. Facts were never the open question.

**The open question is register**, and the scorer cannot see it. Read
`finetune_test_sample.json` by hand and compare `generated` against `reference`.
Specifically: does it write "I did not watch" in the first person the way the
diaries do, or does it fall back to "not observed" the way few-shot did. Does it
reproduce the doubled "became stationary ... it became stationary" construction.
Does it avoid modern phrasing such as "3 fingers in magnitude".

That comparison is the actual result of this run. If the fine-tune matches
few-shot on facts and beats it on register, fine-tuning earned its cost. If it
matches on both, it did not, and prompting is the more maintainable answer,
which plan.md Section 1.5 already counts as a legitimate finding rather than a
failure.

## Known limits going in

- Around 25k target tokens. Small.
- 10 to 15 examples each of acronychal risings and stationary points. The model
  will not learn those properly from this set no matter what sampling is used.
  They will have to lean on the few-shot path.
- Training states are derived from diary text; at inference they will come from
  the celestial engine. If the two formats drift, the model breaks exactly when
  you start using it for real. Worth testing deliberately.
- The register being learned is the Sachs and Hunger English translation, not
  Akkadian. plan.md Section 1 already frames the project that way.
