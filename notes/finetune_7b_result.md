# Qwen2.5-7B QLoRA, 3 epochs (2026-08-16)

The real run. 177 steps, 55.7 min training, 61 min total on one T4.

## Training was clean

| step | 25 | 50 | 75 | 100 | 125 | 150 | 175 |
|---|---|---|---|---|---|---|---|
| eval loss | 0.2384 | 0.1725 | 0.1611 | 0.1537 | 0.1494 | 0.1488 | **0.1487** |

Monotone decrease, no upturn, so no overfitting in the loss sense. It flattens
hard from step 125 (0.1494 to 0.1487 over 50 steps), meaning it converged and
then polished. For comparison the 1.5B smoke run bottomed at 0.2072.

## Scores

| tier | main | held-out |
|---|---|---|
| non-LLM template control | 0/5 | 0/4 |
| qwen2.5:7b zero-shot | 0/5 | - |
| **qwen2.5:7b few-shot (5)** | **5/5** | **4/4** |
| qwen2.5:7b fine-tuned, 3 epochs | 3/5 | 1/4 |
| 1.5B fine-tuned, 1 epoch (smoke) | 2/5 | 0/4 |

**The fine-tune loses to few-shot on facts.** Not close.

## But it wins on register, which is what it was for

Register scorer over the 25 held-out pairs:

| diary marker | reference | generated | |
|---|---:|---:|---|
| watch phrase | 24 | 23 | kept |
| cubit and finger units | 35 | 32 | kept |
| ordinal night dating | 27 | 25 | kept |
| month roman numeral | 12 | 9 | kept |
| 'being N cubits' latitude | 1 | 2 | kept |
| 'having passed' | 4 | 2 | thin |
| degree sign | 1 | 0 | lost |
| 'measured' qualifier | 1 | 0 | lost |

**Zero modern drift on all seven checks.** No "not observed", no "in magnitude",
no spelled-out degrees, no explanatory asides. Few-shot failed exactly there: it
replaced first-person "I did not watch" with "not observed" every time and wrote
"3 fingers in magnitude". The fine-tune does neither. Mean words per entry 19.7
against the reference's 22.4, so it kept the terseness too.

On common conjunctions it is often character-exact:

> ref: Night of the 13th, first part of the night, Venus was 2 1/2 cubits above α Tauri
> gen: Night of the 13th, first part of the night, Venus was 2 1/2 cubits above α Tauri

## Why the facts failed: degeneration, not ignorance

Every fact failure is the model looping or padding, not misunderstanding:

- **bab-05** repeats "it was bright, earthshine was present, it was bright, it
  stood low to the sun" then invents a second month, invents γ Virginis, emits
  the placeholder `x°`, and trails off mid-clause.
- **bab-04** emits `x°` and invents an entire extra observation on "the 20th".
- **bab-03** states the correct entry, then states it again verbatim.
- **gen-02** repeats "last appearance" four times, emits `the xth`, and ends with
  **"medium confidence"**, the state's `confidence` field leaking into prose.
- **gen-03** generates four different nights and loses Sirius and Gemini.
- **gen-01** invents `α Virginis` alongside the correct `β Virginis`.

The pattern is sharp: on the 319-example conjunction class it is near-perfect.
On the long or rare structures it produces the right opening and then cannot
stop. That is classic small-corpus behaviour at 25,644 target tokens.

## Two scorer gaps this run exposed

Criterion (g) was added after seeing these outputs, so it deserves stating
plainly that it was not invented to make the run look bad. Both defects were
**predicted in `notes/finetune_smoke.md`** after the 1.5B run: "state syntax
leaking into the output" and the repetition tic were both flagged as things to
watch at 3 epochs. They got worse, exactly as expected.

1. **Invented stars passed the object whitelist.** The state named β Virginis and
   the model added α Virginis. The whitelist only sees "Virginis", so a star
   swapped for another in the same constellation was invisible. Now checked by
   exact Greek-letter token.
2. **State syntax and placeholders passed everything.** "medium confidence",
   `the xth` and `x°` are not objects, not omens and not relations, so criteria
   (a) to (f) had nothing to say about them.

With (g) active the main set drops 3/5 and the held-out set drops 3/4 to 1/4.
Those are the honest numbers.

## What this means

**Fine-tuning delivered the thing it was supposed to deliver and failed at the
thing prompting had already solved.** That is a cleaner result than either a win
or a loss, and it points somewhere specific rather than nowhere.

The fact failures look like a **decoding** problem more than a training problem.
Generation ran at `temperature=0.7, do_sample=True`, with **no repetition
penalty** and `max_new_tokens=160`. Every failure above is a sampling loop or an
over-long continuation. That is the cheapest possible thing to test, and it needs
no retraining because the adapter is saved.

## Recommended next step, in order of cost

1. **Re-decode, do not retrain.** Load the saved adapter and regenerate with
   `repetition_penalty=1.15`, `no_repeat_ngram_size=6`, and a shorter
   `max_new_tokens` around 80, which is well above the 22-word reference mean.
   If that recovers the fact score while keeping the register, fine-tuning has
   earned its cost outright.
2. If looping persists, **retrain at 2 epochs** rather than 3. Eval loss was
   already flat from step 125, so the third epoch bought 0.0007 of loss and
   plausibly cost generation discipline.
3. Only after those, consider `LORA_R=8`.

## The honest position if re-decoding does not fix it

Few-shot gets the facts right and the register wrong. The fine-tune gets the
register right and the facts wrong. If neither can be pushed to both, the
sensible architecture is the obvious one: **few-shot prompting for the rare
phenomena, the fine-tune for the common ones**, chosen per phenomenon class from
the training counts, which are already known.
