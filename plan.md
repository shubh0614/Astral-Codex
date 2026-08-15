# Project Plan: Sky-Omen Diary Generator (working title)

*Personal research project — non-commercial. This doc is the full handoff brief. Paste it (or point Claude Code at it) to resume work in a new session.*

**Revision history:**
- v1: original plan.
- v2: incorporated round-1 external stress-test (3 LLMs) — genre-split schema, vertical-slice workflow. See `plan_v1_archive.md`.
- v3: incorporated round-2 external stress-test (2 more LLMs) — refined guardrail mechanism, two-layer astronomy engine, calendar normalization as first-class component, concrete Phase 0 decision rule. See `plan_v2_archive.md`.
- v3.1: incorporated round-3 external stress-test (1 more LLM) — tightened gates, no architecture change. See `plan_v3_archive.md`.
- **v3.2 (this version) — LOCKED.** Incorporated round-4 external stress-test (2 more LLMs, 8 total independent reviews across 4 rounds). Both round-4 reviews confirmed the architecture is done and only tactical/empirical items remain. Changes: explicit frozen research question (Section 1.5), LLM-as-judge demoted to secondary evidence behind a deterministic whitelist + hand-built adversarial test set, concrete Babylonian calendar-complexity caveat, concrete vision-extraction cost/testing gate, concrete pass/fail definition for the prompt-only baseline, uncertainty qualifiers added to the observation-state schema, and a practical Kaggle session-length tip. See `plan_v3.1_archive.md` for the pre-lock version.

**This plan is locked. No further stress-testing rounds are planned.** Eight independent LLM reviews across four rounds have now converged on the same instruction every time: the architecture is sound, the remaining unknowns are empirical (corpus size, extraction difficulty, whether fine-tuning is even needed), and the only way to resolve them is to run Phase 0 and look at real data. If you're reading this in a future session and considering another review pass, don't — bring back results from Phase 0 instead.

---

## 0. What Changed (read this first if resuming after a gap)

**v2 → v3 changes, in order of importance:**

1. **Guardrail split into hard facts vs. interpretation.** The old single "FACTS" block conflated things that must never change (which planets, what event, what date) with things that are supposed to be generated (the omen's meaning, the emotional register). A regex/NER validator can confirm mentioned objects but can't catch a hallucinated extra object, a reversed relationship, or tell invented facts apart from legitimate interpretation. Fixed by splitting the schema — see Section 2.
2. **Astronomy engine now has two layers**: physical state (RA/Dec/magnitude/etc.) and a semantic event-detector layer sitting on top of it, producing labels like `close_conjunction` directly — the LLM should never have to learn that "1.7° separation" means "close." This also makes counterfactual testing much cleaner.
3. **Visibility modeling moved into V1 scope** (was previously unaddressed). Position isn't the same as observability — first/last visibility is central to what Babylonian diaries actually record.
4. **Calendar Normalization Layer** promoted to a first-class architecture component, sitting between historical source dates and the astronomy engine. Maya specifically doesn't need to touch the astronomy engine at all — it has its own calendar-only path.
5. **"One training example" now explicitly defined** as one coherent observation/event, not one source text/tablet — this means the real Babylonian and Korean corpora are larger in observation-count than their text-count suggested.
6. **Phase 0 gets a concrete decision rule** for the still-open 3-vs-5 traditions fork: track a usable/ambiguous/reject rate per tradition, decide from that data (Section 7).
7. **Concrete implementation paths added** for two previously-open items: Maya katun mapping (GMT correlation constant 584283, open-source converters exist) and Korean table extraction (use a vision-capable LLM on PDF screenshots, not OCR/manual copying).
8. **Evaluation reprioritized** into core vs. secondary, and the counterfactual test made quantitative (Section 8).

---

## 1. Concept

A hybrid system, two halves:

1. **Deterministic celestial/calendar engine** (not trained) — computes the physically or calendrically relevant state for any date or cycle, past or future. ("Astronomy engine" was the old term; "celestial/calendar engine" is more accurate now that Maya's path is calendar-only, not astronomical.)
2. **Small fine-tuned LLM** — takes that computed state and generates historically-grounded text in the register of a real tradition.

Core design principle: sky/calendar state is computed deterministically from explicit physical or calendrical models — no ML needed there. (Not "solved physics or solved mathematics" — the calendar normalization layer specifically can involve interpretive/conventional assumptions, e.g. intercalation decisions, not just pure calculation. Precision matters here since the architecture leans on this distinction.) The generative part is the *interpretive framework* layered on top, and that varies by tradition and genre.

### Frozen Research Question (new, v3.2 — this is what "success" means now)

> Can deterministic celestial/calendar state be used as a controllable conditioning signal for historically grounded text generation, while preserving hard observational facts and adapting to different historical genres?

This is now the actual success criterion — everything else is instrumentation. Consequences of freezing it this way:
- If Maya gets cut in Phase 0 (empirical gate, Section 7) — the project still succeeds.
- If Vedic gets cut — the project still succeeds.
- If Korean extraction turns out too painful and gets narrowed to one phenomenon — the project still succeeds.
- If the prompt-only baseline turns out sufficient and QLoRA is never needed — the project still succeeds. (This would itself be an interesting finding, not a failure: "a sufficiently capable base model plus structured conditioning reproduces the desired register without fine-tuning" is a real result.)
- Even if the final working system is only a 1.5B model — the project still succeeds.

Don't let scope pressure quietly redefine success as "all five traditions, fully fine-tuned, at 7B+." That was never the actual bar.

**Honest framing:** this is a **historically grounded sky-to-text generator**, not an "authentic historical voice" reconstructor. Even the "real" historical sources are filtered through a specific translator's register. Claim grounded reconstruction inspired by surviving textual conventions — not authenticity.

**Guardrail (non-negotiable, mechanism in Section 2):** physics/calendar supplies hard facts, never freely generated. Culture/tradition supplies interpretation, which is *supposed* to be generated — the guardrail protects the former, evaluates (doesn't block) the latter.

---

## 2. Technical Architecture

### Celestial/Calendar Engine (two-layer, plus calendar normalization)

```
historical source date (any calendar system)
        ↓
CALENDAR NORMALIZATION LAYER
  — parses the source calendar (Babylonian lunisolar, Roman consular,
    Maya Long Count, Korean lunisolar, etc.)
  — converts to a canonical temporal representation
        ↓
PHYSICAL ASTRONOMY LAYER (Skyfield + DE441)
  — RA/Dec, altitude/azimuth, elongation, phase, magnitude
  — explicit convention: apparent geocentric positions, document
    ΔT/precession assumptions as they come up — don't need to solve
    every historical-precision question on day one, but the engine's
    convention must be stated, not implicit
        ↓
VISIBILITY LAYER (new, V1 scope — not deferred)
  — altitude + solar depression + angular separation from Sun +
    apparent magnitude → coarse visible / marginal / not-visible
    classification. Refine later; don't skip in V1 — this is central
    to what "first/last visibility" observations actually record.
        ↓
SEMANTIC EVENT DETECTOR LAYER (new)
  — converts raw physical state into labeled events the LLM can
    condition on directly:
    { "event": "close_conjunction", "objects": ["Jupiter","Saturn"],
      "separation_deg": 1.7 }
  — the LLM should never have to learn that a separation number
    means "close" — that judgment belongs in deterministic code.
        ↓
    → feeds the LLM (Babylonian/Korean/Roman/Vedic paths)

Maya path is separate and does NOT go through the astronomy layers:
historical/target Gregorian date
        ↓
MAYA CALENDAR CONVERTER (GMT correlation constant 584283 — solved,
  open-source Python implementations exist)
        ↓
Long Count → Calendar Round → Katun
        ↓
    → feeds the LLM (prophecy path)
```

**Maya trap to avoid:** a Gregorian date maps cleanly to a katun via the calendar converter — but that does *not* mean every date in that katun should generate "the" textual prophecy associated with that katun number. Keep "calendar state" (deterministic) and "historically attested prophetic association" (from the actual Chilam Balam text) as separate concerns. Don't recreate the forced date-alignment problem one level up.

### Task Schema

Every tradition gets a shared outer structure, branches into genre-specific inner structure, and — for Babylonian specifically — a three-way split to avoid conflating historical text with modern reconstruction:

```json
{
  "tradition": "babylonian | roman | vedic | maya | korean",
  "genre": "observation | omen_interpretation | prophecy",
  "historical": { "text": "...", "observations": [...] },
  "computed": { "sun": {...}, "moon": {...}, "events": [...] },
  "alignment": {
    "conversion_method": "...",
    "astronomical_match": "direct | inferred | reconstructed | none",
    "match_confidence": 0.87,
    "source_basis": "primary observation | scholarly reconstruction | rule text"
  },
  "generation": { "observation_state": {...}, "text": "..." }
}
```

The `alignment` block is what prevents accidentally training "modern astronomical interpretation disguised as ancient observation" — always know which category a given data point falls into.

**Genre 1 — Observation** (Babylonian, Korean): `date → computed state → dated observational-register text`.

**Genre 2 — Omen Interpretation** (Roman, Vedic): `event pattern → culturally specific interpretation in period voice`, no exact date-to-sky match required. Note: Vedic specifically is richer than a flat "omen" bucket — Brihat Samhita spans omen rules, celestial interpretation, and calendrical/seasonal signs. Don't lock into one sub-genre; it's fine to keep `omen_interpretation` as the working label for v1 but expect this to split further once real examples are in hand.

**Genre 3 — Prophecy** (Maya): `katun state → prophetic/ritual narrative`, via the calendar-only path above.

### Guardrail Mechanism (revised — hard facts vs. interpretation)

**Old flaw:** a single "FACTS" block and a regex check that only confirms mentioned-objects-present, which can't catch hallucinated additions, reversed relationships, or distinguish invented facts from legitimate interpretation.

**Fixed structure:**

```
<TRADITION=BABYLONIAN>
<GENRE=OBSERVATION>
<OBSERVATION_STATE>
  Venus: visible, elongation 32°, magnitude -3.9, confidence: high
  Moon: waxing crescent, near Jupiter, first_visibility: possible, confidence: medium
  Events: [{"event":"conjunction","objects":["Moon","Jupiter"],"separation_deg":1.2}]
</OBSERVATION_STATE>
<ENTRY>
[generated text]
</ENTRY>
```

**Uncertainty qualifiers (new, v3.2):** carry a `confidence` field on every observation from day one, not just on the alignment/provenance block. Babylonian diaries specifically flag first/last visibility as observationally uncertain — don't let the computed astronomy present false precision the historical record itself doesn't have.

- **Hard facts** (must never change): date, which objects, event type, relative position, phase, visibility, conjunction/eclipse presence. Validated strictly.
- **Interpretation** (allowed, expected, the actual point of omen/prophecy genres): omen meaning, consequence, register, ritual framing. Evaluated for quality/genre-fit, not blocked.
- **Validation hierarchy (revised, v3.2)** — don't let "model A judged by model B" become the primary scientific evidence:
  1. **Deterministic whitelist/NER** (primary): only the objects/event-types present in OBSERVATION_STATE are permitted to appear in the output — a hard-coded whitelist of the ~7 planet names + Sun/Moon + known event types catches most violations mechanically.
  2. **Hand-built adversarial test set** (primary evidence): construct ~30–50 manual cases of the form `OBSERVATION_STATE X → OUTPUT Y`, some matching, some deliberately wrong (wrong planet substituted, relationship reversed, extra object added). This is where real confidence should come from, not from the LLM judge.
  3. **LLM-as-judge** (secondary/convenience only): catches the semantic leftovers the whitelist and manual set miss — e.g. "Jupiter" and "Mercury" conflated in ambiguous phrasing. Useful, not ground truth.
- **Optional technique worth trying**: negative examples — under `<GENRE=OBSERVATION>`, explicitly train against adding interpretive claims that don't belong to that genre/tradition, to reinforce the observation≠interpretation boundary directly rather than only via the validator.

### What counts as "one training example" (new, was undefined)

**Define it as one coherent observation/event, not one source text/tablet.** A single Babylonian diary tablet or Korean chronicle entry can contain many separate nightly observations (e.g. entries for the 2nd, 4th, 6th, 7th, 8th of a month, each independently mappable to a sky state). Counting at the text/tablet level undercounts the real corpus significantly. This matters most for Babylonian (real corpus likely thousands of observation-units, not "401 texts") and Korean (don't pre-target "25,000" — think in terms of a realistic funnel: raw records → extractable → date-resolved → astronomy-mappable → clean usable examples, and let Phase 0/2 tell you the real number at each stage).

**Sequence question (flag, don't solve yet):** should consecutive nights from the same source become independent training examples, or connected sequences? Start at the independent event level for v1 — sequence modeling is a legitimate later refinement, not a v1 blocker.

### Base model for fine-tuning
- **Training happens on Kaggle** — 30 GPU-hrs/week, P100 (16GB) or T4x2 (32GB), 12-hr session cap.
- **Model-size ladder:** 1.5B → 3B → 7B. Do not jump to 13B without evidence 7B is under-capacity.
- **Three-tier baseline comparison, not one** — run all three before deciding fine-tuning is worth its cost:
  1. Raw 7B model, zero-shot (`OBSERVATION_STATE → generation`)
  2. Raw 7B model, few-shot (2–5 historical examples in the prompt)
  3. QLoRA fine-tuned
  - Also worth a **non-LLM template baseline** ("When [OBJECT] appeared [RELATION] [OBJECT], [traditional consequence]") — if the fine-tuned model only marginally beats a dumb template on style, that tells you something important about where the value actually is.
  - **Fine-tuning is conditional, not the default path.** Proceed to QLoRA only if the prompting/few-shot baseline fails specific evaluation checks (Section 8, especially the style/blind-test criteria). If a 7B model with good few-shot prompting already produces plausible, factual, stylistically-in-the-ballpark output, that's the more maintainable outcome — no GPU quota spent, no LoRA-version-compatibility fragility, faster iteration. Treat fine-tuning as an optimization pursued on evidence of need, not an assumed step.
- License note: Qwen2.5 is Apache-2.0 (cleaner for any future redistribution); Llama 3.1 has Meta's Community License with redistribution conditions.
- **LoRA / QLoRA**, not full fine-tuning. Tag format: `<TRADITION=...><GENRE=...>`.
- Local GTX 1650 4GB laptop: dev/testing/tokenization only.
- **Practical tip (new, v3.2):** cap the first Kaggle training runs at ~2 hours, not the full 12-hour session limit. Train 1–2 epochs on the 1.5B model, checkpoint, download, test inference locally — the failure mode to avoid is burning a third of the weekly 30-hour quota on a run with a data-loader bug or a learning rate off by 10×. Checkpoint early, validate often, extend session length only once the pipeline is proven.

### Tradition balancing
Raw corpus sizes will be wildly uneven. Use controlled/equal sampling per tradition regardless of raw counts, not proportional sampling — otherwise the largest corpus (likely Korean) becomes the model's default voice.

### Hosting (later phase, not v1 concern)
Prototype: HF Spaces/Inference Endpoint. Production: GGUF + llama.cpp, revisit once model size is chosen.

---

## 3. Copyright / Licensing Posture

Personal, non-commercial — reduces practical risk, doesn't eliminate copyright law outright. Treat as a project-management decision, not a settled legal conclusion. Revisit source-by-source if this ever moves toward public release (dataset, weights, and a public site are three separate exposure questions, not one). Site-level database/terms-of-use rights are separate from copyright in the underlying ancient text — don't conflate if scraped modern sources get added later.

---

## 4. Data Sources — V1 (five traditions)

Genre + fetch notes (see `plan_v2_archive.md` for the full original per-source detail — links unchanged, repeated here only where notes changed):

### 1. Roman — Julius Obsequens, *Liber Prodigiorum*
Genre: omen_interpretation. Dated by year/consulship, not night — condition on event *patterns*, not nightly sky state. Full translation: attalus.org/translate/obsequens.html. Fetch difficulty: lowest.

### 2. Vedic — Brihat Samhita
Genre: omen_interpretation (working label — richer than this, see Section 2 genre note). Chapters 3–10, 11, 46. Full 1946/47 translation on archive.org. Fetch difficulty: low.
**Voice-thinness risk (new, round 3):** Brihat Samhita reads as legalistic/prescriptive rules ("when Mars enters Magha, the king dies"), not narrative prose. "Generating period voice" for Vedic risks becoming paraphrase-with-archaic-grammar rather than genuine stylistic transfer — this is the weakest of the five traditions for demonstrating real voice generation. **Watch for this explicitly in Phase 0.** If it holds, a legitimate fallback is treating Vedic as a lookup-table tradition rather than a fully generative one: engine detects the astronomical condition, system pulls the matching Brihat Samhita rule, model (if any) only lightly renders it in archaic-register English rather than inventing narrative padding around it.

### 3. Maya — Books of Chilam Balam
Genre: prophecy. Keyed to katun via the calendar-only path (Section 2) — GMT correlation constant 584283 for Gregorian↔Long Count conversion, open-source Python implementations exist. **Do not assume every date in a katun maps to "the" textual prophecy** — keep calendar-state and historically-attested-association separate (Section 2 trap note). Full translation (Roys, 1933) on sacred-texts.com. Fetch difficulty: low-medium.
**Katun-repetition UX problem (new, round 3):** a katun is ~19.7 years — a day-granularity date slider will return the *same* prophecy text for two decades straight unless sub-katun variation is added. **Before any ML work**, write a standalone script (no model involved): Gregorian date → Long Count → katun → looked-up prophecy from a small hand-curated table. Slide through dates manually and check whether the experience feels interesting or just repetitive. If repetitive, this is a design problem to solve before touching fine-tuning, not a downstream polish item.

### 4. Babylonian — ORACC ADsD + Attalus.org
Genre: observation. **Build the vertical slice here first.** Real corpus is likely thousands of observation-units once counted correctly (Section 2) — individual diary entries record multiple separate nights, not one observation per text. **Cleaning note (new):** raw translations contain `[...]` markers for tablet damage/gaps — filter or manually patch heavily fragmentary examples during Phase 1 cleaning, or the model will learn to generate `[...]` as a stylistic tic. Fetch difficulty: medium.
**Clean-triple count gate (new, round 3):** before writing any training code, manually tally how many entries have (a) a recoverable date — year + month minimum, (b) at least one specific astronomical observation, not just weather/river-level notes, and (c) a continuous English text of more than two sentences. **If that count is under ~60, do not force Babylonian as the vertical slice.** Two specific fallbacks, not "force it anyway": (1) expand the gate criteria to responsibly include partially-fragmentary entries if they're still usable, or (2) commit to the prompting-only architecture for Babylonian specifically rather than training on data that doesn't really exist yet. This sharpens the existing Phase 0→1 gate item below, doesn't replace it.

**Calendar complexity caveat (new, v3.2):** Babylonian dates are genuinely nasty, not just a formatting exercise. Regnal years require a king-list conversion table. The calendar was lunisolar with intercalary months (an extra Addaru or Ululu) inserted by decree or observation in earlier periods — not a fixed mathematical rule. This means "Year 10 of Artaxerxes, month Nisannu" doesn't always resolve to one exact Gregorian date — sometimes only a range, or scholarly-consensus-dependent. **Use the `alignment` block's confidence score and match-type field for this** (Section 2) — some dates will legitimately carry `match_confidence: 0.6` and a ±2-day range. Document the uncertainty, don't hide it. Some tablets may not be date-normalizable at all without external scholarly reference tables — that's expected, not a bug in your pipeline.

### 5. Korean — via astronomy-history academic papers
Genre: observation. Don't pre-target "25,000" as the goal — think in terms of a realistic extraction funnel (Section 2) and let real numbers emerge. **Extraction method correction:** don't attempt manual copy-paste or traditional OCR on the academic PDF tables — screenshot the tables and use a vision-capable model (Claude, GPT-4o, or similar) with a direct "extract this table to strict JSON" prompt. Turns a multi-week manual task into a short scripted one. Start with one paper, gauge real effort, before committing further. Fetch difficulty: highest, but by far the largest potential corpus.
**Fallback if extraction is worse than expected (new, round 3):** older astronomy-history papers (1990s–2000s, common in this niche) sometimes embed tables as scanned images or broken LaTeX that resist even vision-model extraction. If that's the case after the first paper, don't chase the full ~25,000-record harvest — narrow v1 Korean scope to **one well-documented phenomenon** (e.g., Halley's Comet appearances only, or lunar eclipse records only). A clean 200-example subset beats a messy, partially-broken 2,000-example grab bag.

**Vision-extraction reality check (new, v3.2):** budget real API cost for this — $20–50 if processing 500+ pages of tables, not $0. Academic astronomy tables often have multi-row headers, merged cells, footnotes, and mixed Chinese/Japanese/Latin characters, and vision models can hallucinate row alignment or miss footnote markers that distinguish "observed" from "inferred" dates. **Test the extraction approach on ONE table before committing to it as the primary path.** If the first table comes back with >30% field errors, switch to the narrow-scope fallback immediately — don't spend weeks iterating on extraction prompts.

---

## 5. Data Sources — V2 Backlog

(Unchanged from v2 — Egyptian, Islamic, Persian/Zoroastrian, Aztec/Nahua, European medieval, Vietnamese. See `plan_v2_archive.md` Section 5 for full detail. Run each through the Phase 0 viability check before full fetch, same as v1 traditions.)

---

## 6. Explicitly Excluded / Deprioritized

(Unchanged — Aboriginal Australian [ethical exclusion], Minoan, Olmec, Inca, most oral traditions, Japan/Onmyōdō, China/Kaiyuan Zhanjing, Greece/Aratus, Buddhism/Jainism, CCAG, Book of Enoch Astronomical Book. Full list and reasons in `plan_v2_archive.md` Section 6 — reasons still hold, do not re-litigate without new info.)

---

## 7. Workflow Phases

**Phase 0 — Corpus Viability Sprint (revised counts + explicit decision rule)**
- Pull raw examples: **20–30 for Roman, Vedic, Maya, Korean; 50–100 for Babylonian** (Babylonian gets more because it's the vertical-slice reference — the others just need schema discovery, not statistical validation).
- Manually annotate each against: is there a date/cycle-position? can a meaningful state be determined? is this observation, interpretation, or rule-text? does it match its assigned genre?
- **Track a usable / ambiguous / reject rate per tradition.** This produces an empirical table like:

  | Tradition | Candidates | Usable | Ambiguous | Reject |
  |---|---|---|---|---|
  | Babylonian | 100 | ? | ? | ? |
  | Korean | 30 | ? | ? | ? |
  | Roman | 30 | ? | ? | ? |
  | Vedic | 30 | ? | ? | ? |
  | Maya | 30 | ? | ? | ? |

- **3-vs-5 decision rule (resolves the open fork from v2):** decide from this table, not philosophically. If a tradition's usable rate collapses (roughly ≤20%) while the others hold up well above it, cut that tradition to v2. If all five hold up reasonably (even unevenly, e.g. 60–95%), keep all five — the genre-split architecture exists specifically to accommodate this variation.
- Target: ~10–15 hours total.

**Phase 0 → Phase 1 gate — explicit checklist, don't proceed until all true:**
- [ ] Babylonian corpus has ≥50 clean observation units
- [ ] Historical dates can be normalized (calendar layer works for at least Babylonian)
- [ ] ≥80% of sampled Babylonian observations map to structured events
- [ ] Celestial engine reproduces the relevant event classes
- [ ] Visibility assumptions are documented (even if coarse)
- [ ] OBSERVATION_STATE / hard-facts-vs-interpretation schema is stable
- [ ] Prompt-only baseline produces coherent (if imperfect) output — **concrete pass/fail (new, v3.2):** given 5 hand-crafted observation states, the 7B few-shot prompt generates text that (a) mentions all objects present in the state, (b) mentions no objects absent from it, and (c) reads as a single dated entry, not a list of facts. Passing 4/5 → proceed. Passing ≤1/5 → the prompt itself needs work before any fine-tuning discussion is worth having.
- [ ] Factuality validator (regex + LLM-judge) works on hand-built test cases

**Phase 1 — Babylonian Vertical Slice**
- Full fetch, clean (including fragmentary-text handling above), schema-structure, for Babylonian only.
- Build the celestial/calendar engine module standalone and testable.
- Wire the guardrail mechanism, run the three-tier baseline comparison, do the first QLoRA fine-tune (1.5B dev model).
- Run the evaluation suite (Section 8).
- **Success definition for this phase (concrete, not vague):** given a date and a structured Babylonian observation state, the system generates an entry that (a) preserves the hard facts, (b) responds meaningfully to counterfactual changes to those facts, and (c) is judged more Babylonian/diary-like than the raw prompting baseline by a blind evaluator. If achieved, the core project has worked — everything after is scale.
- **Do not proceed to other traditions until this gate is met.**

**Phase 2 — Horizontal Scale-Out**
- Order: Korean (same genre, easiest add) → Roman/Vedic (introduce omen_interpretation) → Maya (introduces prophecy, biggest structural departure, last).
- Re-run Phase 0 per new tradition if not already done. Apply tradition-balancing sampling once multiple traditions are in the mix.

**Phase 3 — Multi-Tradition Fine-Tune**
- Combine into one tagged multi-tradition, multi-genre model.
- Re-confirm fine-tuning still earns its cost against the baselines.
- Model-size ladder per Section 2.

**UI remains explicitly out of scope.**

---

## 8. Evaluation (reprioritized — core vs. secondary)

**Core (this is what the research question actually hinges on):**

**A. Factuality** — regex/NER for hard-fact presence, plus LLM-as-judge for hallucinated additions/reversed relationships (Section 2).

**B. Conditioning sensitivity (quantified counterfactual test)** — take a real example, change only the hard facts (e.g. swap "Venus near Moon" for "Mars near Moon"), generate ~20 outputs per condition, measure mention accuracy and divergence. Want: Venus-mentions high & Mars-mentions near-zero under condition A, and the reverse under condition B. If outputs barely change across conditions, conditioning isn't actually working — this is arguably the single most important number in the whole project.

**C. Genre fidelity** — does an observation-genre output stay descriptive (no invented interpretation), does an omen-genre output actually interpret?

**D. Tradition fidelity (blind human eval)** — can an evaluator correctly guess tradition/genre from unlabeled outputs, significantly above chance?

**E. Generalization** — feed a sky/calendar state never seen in training, confirm genuinely new (not memorized-and-recombined) output.

**Evaluation ceiling — be honest about it (new, round 3):** tests B and D require distinguishing Babylonian register from Korean from Roman from Maya, which realistically means *you* are the evaluator, and you are not simultaneously an Assyriologist, a Joseon court historian, and a Yucatec Maya specialist. That's fine for a personal project, but the blind test measures "sounds plausibly ancient to an informed layperson," not scholarly authenticity — don't let it create false confidence. **Tests A (factuality), B (conditioning sensitivity via the counterfactual test), and E (generalization) are auto-checkable and are the real load-bearing evidence.** Human-judged tests C and D are useful signal, not proof.

**Secondary (interesting, not central — don't let these consume core research time):**

**F. Memorization/contamination check.**

**G. Adversarial/impossible-input test** — deliberately contradictory sky state, see if the model shows any sensitivity to it. Good stretch research thread if the core project succeeds early; not a v1 priority.

---

## 9. Open Questions / Decisions Still Needed

- [x] ~~Maya katun-cycle mapping implementation~~ — resolved: GMT correlation constant 584283, open-source converters exist (Section 2).
- [x] ~~Korean PDF-table extraction approach~~ — resolved: vision-capable LLM on screenshots, not OCR/manual (Section 4).
- [ ] **3-vs-5 traditions fork** — has a concrete decision rule now (Section 7 Phase 0), still needs real data to resolve. Not a philosophical question anymore. **Round-3 note:** one reviewer argued a priori for cutting to 3 now (drop Vedic and Maya), citing Vedic's voice-thinness risk and Maya's katun-repetition problem (both now flagged in Section 4). This raises the prior probability that Vedic/Maya get cut once real Phase 0 numbers come in — but it isn't a reason to skip the empirical gate two prior rounds of review already agreed on. Wait for the usable/ambiguous/reject table.
- [ ] Final base model choice — resolve via the three-tier baseline comparison (Section 2) before committing.
- [ ] Vedic sub-genre splitting (omen_rule / celestial_interpretation / calendrical_sign) — keep flat `omen_interpretation` for v1, revisit once real examples are in hand.
- [ ] Sequence-context modeling (independent nightly events vs. connected sequences) — deferred, not a v1 blocker.
- [ ] Whether to use synthetic-alignment (LLM-generated training pairs) as a bootstrap for thin traditions — still open, still secondary to real historical grounding. **Round-3 addition: if used, cap synthetic examples at ~30% of any single tradition's training set.** Beyond that fraction, you're training an echo of an echo rather than bootstrapping from real material — use it to seed style, not to replace primary sources.

---

*End of plan. See `continuity.md` for session-to-session state and `CLAUDE.md` for working rules. Next action: Phase 0, not more planning.*
