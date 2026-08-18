# Re-decoding the 3-epoch adapter (2026-08-19)

Decode-only rerun of the saved adapter, four settings, 10.7 min on one T4. Two
findings, and the second one retracts something from `notes/finetune_7b_result.md`.

## Scores

| config | main | gen | register markers | modern drift | corrupted tokens |
|---|---|---|---|---|---:|
| `orig` (t=0.7, no penalty, 160 tok) | **4/5** | **3/4** | 7 kept, 2 lost | 0 | **0** |
| `greedy` (+rep 1.15, no-repeat-6, 80 tok) | 0/5 | 1/4 | 7 kept, 2 lost | 0 | 13 |
| `sampled` (t=0.7, same guards) | 1/5 | 0/4 | 5 kept, 4 lost | 0 | 6 |
| `greedy_firstline` | 0/5 | 1/4 | 7 kept, 2 lost | 0 | 13 |
| previous run, same settings as `orig` | 3/5 | 1/4 | 7 kept, 2 lost | 0 | 1 |

## Finding 1: the repetition penalty made it worse, and the reason is specific

Every penalised config scored **at or below the original**. Not marginally: 0/5.

The mechanism is visible in the text. `repetition_penalty=1.15` downweights any
token already in the context, and the diaries' register **is** repetition. The
same nouns recur in every clause, so the penalty pushes the model off the correct
token onto its nearest neighbour:

| reference | `greedy` output |
|---|---|
| 1 cubit 8 fingers | 1 cubit 8 **finger** |
| 1 1/2 cubits behind Jupiter | 1 1/2 **cubes** behind Jupiter |
| Night of the 11th | Night of the **11tih** |
| Night of the 24th | Night of the **24tih** |
| back to the west | back to **thw** west |

Zero such corruptions in `orig`, 13 in each greedy config. Criterion (e) then
fails on the corrupted measurement, which is why the score collapses: the model
still knows the fact, it can no longer spell it.

`no_repeat_ngram_size=6` is wrong here for the same reason. "clouds, I did not
watch;" is a six-gram the diaries repeat constantly and legitimately.

**So the remedy in `finetune_7b_result.md` was wrong even though the diagnosis
was right.** The failures were loops, but a repetition penalty is the one tool
that cannot fix loops in a corpus whose register is repetition. Recorded rather
than quietly dropped, because it is the more useful half of this run.

`greedy_firstline` is byte-identical to `greedy` on every case, so no output ran
past a newline. The over-long continuations were single-line all along and the
first-line trim has nothing to cut.

## Finding 2: the eval set cannot tell these tiers apart

`orig` reproduces the previous run's settings exactly. It scored **4/5 and 3/4**
where the previous run scored **3/5 and 1/4**. Same adapter, same cases, same
config. The only difference is the RNG state, since the previous run generated
without seeding and this one seeds before each config.

**The held-out set moved 1/4 to 3/4 on sampling noise alone.** That is half the
set, from nothing but the seed.

This matters more than anything else here, because the previous session's
headline claim rests on it:

> "The fine-tune loses to few-shot on facts. Not close."

**That claim is not supported.** It compared a single noisy sample of the
fine-tune against a single noisy sample of few-shot. Few-shot's 5/5 and 4/4 are
one draw each and carry the same variance. On this draw the fine-tune scores 4/5
and 3/4, which is inside touching distance, and the direction of the gap is no
longer established.

What survives is the register result, and it survives because it is measured
differently: 25 pairs, eleven marker counts, dozens of observations per cell
rather than nine pass/fail bits. Zero modern drift in all four configs, against
few-shot drifting on every check. That comparison is stable.

## What this changes

1. **9 pass/fail cases is not an evaluation.** plan.md Section 1.5 anticipated
   this, calling for a hand-built 30 to 50 case adversarial set; the 9 were a
   starting point that got treated as the instrument. They should not be used to
   rank two tiers that are close.
2. **Report a distribution, not a number.** Generation is cheap: the whole
   4-config sweep was 10.7 min. Running each tier over 5 seeds and reporting mean
   and range costs almost nothing and is the difference between a measurement and
   an anecdote.
3. **Few-shot needs re-measuring the same way.** Its 5/5 and 4/4 have never been
   repeated. Until they are, the honest statement is that both tiers pass most
   cases most of the time and the register is the only separation anyone has
   actually demonstrated.

## Recommended next step

**Do not retrain, and do not change the decoder.** `orig` is the best config
tested and it is the one already in use.

Build the real evaluation instead: expand the case set toward the 30 to 50 plan.md
asks for, and re-run every tier including few-shot over multiple seeds. Until that
exists, no fact-score comparison between prompting and fine-tuning means anything,
and the 2-epoch retrain would be tuning against noise.
