# Running the fine-tune on Kaggle

`train_kaggle.py` is a standalone Kaggle **Script**, not a notebook. Create a
new Script, paste the whole file, hit Save and Run All. The log comes out linear
and readable: no progress bars, no library warnings, one line per event.

## Settings before you run

- **Accelerator: T4 or T4 x2, not P100.** bitsandbytes 4-bit is unreliable on
  Pascal (the P100 is compute 6.0); the T4 is 7.5. The script checks this and
  warns if it sees a card below compute 7.0.
- **Internet: ON.** The script pulls its data from the public GitHub repo, so
  there is no dataset to attach.

Neither card supports bf16, which is why everything runs fp16.

## Run 1: smoke

Leave `SMOKE = True`. Qwen2.5-1.5B-Instruct, one epoch, a few minutes.

**Not a result.** It exists to prove the data loads, the chat template applies,
the trainer steps and generation produces text, for minutes of quota instead of
hours. That is what plan.md's model-size ladder means by dev-loop testing, and
it already earned its keep once: the first attempt died on a TRL signature
change, which would have been a two hour loss on the real run.

If it finishes and the generation section prints something diary-shaped, move on.

## Run 2: real

Set `SMOKE = False`, run again. Qwen2.5-7B-Instruct, 3 epochs.

**7B specifically, because the baseline was 7B.** qwen2.5:7b with few-shot
prompting already scores 5/5 on the main cases and 4/4 on the held-out set.
Fine-tuning a 1.5B and comparing it to that would measure model size, not
fine-tuning. To ask whether fine-tuning beats prompting, hold the model constant.

933 examples at an effective batch of 16 is about 58 steps per epoch, so roughly
175 steps. Comfortably inside the 2 hour cap.

## What the log will show you

Sections in order: environment, data, model, trainer config, training, loss
curve, generation, done.

**The one that matters is the loss curve.** The training set is about 25,600
target tokens, small enough that memorisation is the realistic failure rather
than undercapacity. The script prints every eval point, names the best step, and
says outright whether eval loss turned upward. If it did, cut to 2 epochs or
drop `LORA_R` to 8. Do not raise the rank.

## Library version handling, and what went wrong twice

**The script no longer upgrades anything.** It installs only packages that are
genuinely absent and never passes `-U`. That matters: forcing an upgrade pulled
transformers 5.15 and trl 1.10 onto the image and broke two runs in a row.
Kaggle's preinstalled set is a tested combination, so leave it alone.

Two failures worth recording, because both were library churn rather than
anything to do with the project:

1. `SFTConfig.__init__() got an unexpected keyword argument 'warmup_ratio'`.
   TRL's config signature had moved. Fixed by asking the installed classes what
   they accept and dropping the rest. The log prints the TRL version, the
   rejected keys and the accepted ones, so a third failure names itself.
2. `'functools.partial' object has no attribute '__func__'` inside
   `_patch_chunked_ce_lm_head`. TRL's chunked cross-entropy optimisation assumes
   `model.forward` is a bound method, but accelerate's `device_map="auto"` hooks
   replace it with a `functools.partial`. Fixed two ways: the model is now
   pinned to one GPU with `device_map={"": 0}`, which avoids the wrapper
   entirely and is the better setup anyway since a 7B in 4-bit is about 5 GB and
   fits one T4; and the chunked-CE patch is switched off if the wrapper is
   detected. It is a memory optimisation, not required for correctness.
3. `Expected all tensors to be on the same device, but got index is on cuda:1,
   different from other tensors on cuda:0`. On a T4 x2 instance the HF Trainer
   sees two devices and silently wraps the model in `nn.DataParallel`,
   replicating it to cuda:1 while the 4-bit weights sit on cuda:0. Fixed with
   `CUDA_VISIBLE_DEVICES=0` at the very top of the script, before torch is
   imported. Using one GPU is the right call regardless: DataParallel is
   deprecated and behaves badly with quantized models, and one T4 has ample
   room. **Selecting T4 x2 on Kaggle is fine, the script just uses one of them.**

## Getting results back

Download from the output pane:

- `finetune_main.json`
- `finetune_gen.json`
- `finetune_test_sample.json`
- `adapter/`, the LoRA weights, worth keeping only if the scores justify it

Put the JSON files in `data/processed/` locally, then:

```
python scripts/score_baseline.py data/processed/finetune_main.json
python scripts/score_baseline.py data/processed/finetune_gen.json
```

The scorer applies the same six criteria used on every other tier and has been
self-tested, so its verdicts mean something.

## The bar

| tier | main set | held-out set |
|---|---|---|
| non-LLM template control | 0/5 | 0/4 |
| qwen2.5:7b zero-shot | 0/5 | - |
| qwen2.5:7b few-shot (5) | 5/5 | 4/4 |
| **qwen2.5:7b fine-tuned** | **?** | **?** |

Matching 5/5 and 4/4 is not a win. Few-shot already does that, and facts were
never the open question.

**Register is the open question and the scorer cannot see it.** That is why the
script also dumps 25 held-out generations next to their references, and prints
the first five in the log. Read them. Specifically: the diaries write
"I did not watch" in the first person and few-shot replaced it with "not
observed" every time. Does the fine-tune recover that? Does it reproduce the
doubled "became stationary ... it became stationary"? Does it avoid modern
phrasing like "3 fingers in magnitude"?

If it matches few-shot on facts and beats it on register, fine-tuning earned its
cost. If it matches on both, it did not, and prompting is the more maintainable
answer, which plan.md Section 1.5 already counts as a real finding rather than a
failure.

## Known limits going in

- About 25,600 target tokens. Small.
- 10 to 14 examples each of acronychal risings and stationary points. The model
  will not learn those properly from this set regardless of sampling; they will
  have to lean on the few-shot path.
- Training states are derived from diary text, but at inference they will come
  from the celestial engine. If the two formats drift, the model breaks exactly
  when you start using it for real. Worth testing deliberately.
- The register being learned is the Sachs and Hunger English translation, not
  Akkadian. plan.md Section 1 frames the project that way already.
