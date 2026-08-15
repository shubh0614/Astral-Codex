# Prompt-only baseline gate: harness built, two holes found in the gate itself

plan.md Section 7, Phase 0 -> Phase 1 checklist item 7. Built 2026-08-15.

Why this was done before the celestial engine: plan.md Section 2 makes
fine-tuning **conditional** on this baseline failing. So this test decides how
big Phase 1 actually is, and it needs no engine, the five observation states
are hand-written from diary entries already on disk.

## What exists now

| file | role |
|---|---|
| `data/processed/baseline_cases.json` | the 5 hand-crafted OBSERVATION_STATEs, each from a real zero-gap diary entry, spanning 5 different phenomenon types |
| `scripts/baseline_prompt.py` | system prompt + 3 few-shot examples (different entries from the 5 cases - no leakage) |
| `scripts/run_baseline.py` | runner for ollama / OpenAI-compatible / Anthropic, plus the non-LLM template control |
| `scripts/score_baseline.py` | deterministic scorer |
| `scripts/selftest_scorer.py` | validates the scorer before it is trusted |

**Not yet run against a real model.** This dev box has no model runner, no API
key, and a 4 GB GTX 1650. Easiest path: `ollama pull qwen2.5:7b`, then
`python scripts/run_baseline.py --backend ollama --model qwen2.5:7b`.

## The scorer is self-tested

A broken scorer would silently decide whether this project needs fine-tuning,
so it gets tested against two fixtures before use:

- **Real historical entries -> 5/5.** They are by definition the right answer.
- **Deliberately broken outputs -> 0/5**, each caught for the intended reason:
  wrong star substituted, extra planet hallucinated, bulleted list instead of
  prose, omen language in an observation entry, required object missing.

Run `python scripts/selftest_scorer.py`. It exits non-zero on failure.

## Two holes in the gate as written

Both found by running the harness, both flagged rather than silently patched,
same handling as the `>2 sentences` issue in `notes/phase0_results.md`.

### (d) The gate did not check genre fidelity

This output satisfies plan.md's stated (a), (b) and (c) completely and would
have **passed**:

> The 13th, Venus' first appearance in the east in Scorpius; **this portends
> that the king will fall and there will be war.**

Every hard fact preserved, no extra objects, one dated prose entry, and an
observation-genre prompt inventing an omen, which is exactly what the guardrail
exists to prevent. Not a new idea: plan.md Section 2 already proposes negative
examples against interpretive claims under `<GENRE=OBSERVATION>`, and Section 8
test C is genre fidelity. The gate checklist just never enumerated it. Added as
criterion (d).

### (e) The gate did not check that hard facts survive: only object names

This is the more serious one, and the non-LLM template control exposed it.

plan.md Section 2 asks for a dumb template control: *"if the fine-tuned model
only marginally beats a dumb template on style, that tells you something
important about where the value actually is."* The template does not marginally
beat anything, **under the gate as written it scored a clean 5/5.**

It got there while dropping, on every single case, facts that were sitting in
the OBSERVATION_STATE:

| case | template dropped |
|---|---|
| moon-star | the watch, "beginning of the night" |
| moon-planet | the latitude clause, "1 cubit high to the north" |
| planet-planet | the watch, "2 fingers", "to the west" |
| heliacal | "in the east", "bright", the "(ideal)" correction |
| lunar first visibility | **the month number IX**, "earthshine", "low to the sun" |

Criterion (a) checks only object *names*, Moon, Venus, Jupiter. A model can
discard every measurement, direction and time-of-night and still pass. For a
project whose entire premise is that hard facts must never change, that is the
wrong thing to measure.

Added criterion (e): the quantitative and qualitative facts must survive, with
each fact given as a list of acceptable surface variants.

**With (e) active the template control scores 0/5**, correct, since it emits a
stub, not a diary entry.

## What this means for interpreting the real run

When a 7B is finally run against this, a high score is **necessary but not
sufficient**. The corrected gate now separates "reproduces the diary" from
"emits a stub", but it still does not measure register, whether the output
*sounds* Babylonian. That is Section 8's tests B and D, and it is the thing
that will actually decide whether QLoRA earns its cost.

The concrete comparison to make is three-way, all against the same 5 cases:
template control (0/5, known) -> 7B few-shot -> 7B zero-shot. If the 7B cannot
beat 0/5 by a wide margin, the prompt is the problem, not the model.
