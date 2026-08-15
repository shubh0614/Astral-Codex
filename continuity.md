# Continuity Log

**READ THIS FILE FIRST, EVERY SESSION, BEFORE DOING ANYTHING ELSE.**
**UPDATE THIS FILE LAST, EVERY SESSION, BEFORE ENDING, even if the session was short or exploratory.**

This file exists because the project spans many sessions and Claude Code has no memory between them. This is the single source of truth for "where are we." `plan.md` is the stable reference (what we're building); this file is the moving log (what's actually been done, and what's next).

---

## How to use this file (rules for Claude Code)

1. On session start: read this file top to bottom, then read `plan.md` Section 8 (Workflow Phases) to confirm current phase.
2. Do not skip ahead a phase. If Phase 1 (data fetch) isn't marked complete for all 5 v1 traditions, do not start Phase 2 work unless the user explicitly says to.
3. Do not re-decide things already logged in "Key Decisions Log" below: if you think a past decision was wrong, flag it to the user and ask, don't silently override it.
4. Before ending a session (or when told to wrap up), update:
   - "Current Phase / Status" section
   - "Last Session Summary"
   - "Next Immediate Steps"
   - Append to "Key Decisions Log" if any new decisions were made
   - Append to "File Map" if any new files were created
5. Keep entries terse. This is a status log, not a diary: one or two lines per item, not paragraphs.

---

## Current Phase / Status

**Phase:** 1, Babylonian Vertical Slice. Data layer and celestial engine are built. Model layer not started.
**Status:** Phase 0 is complete except the Korean annotation pass. Phase 1 has begun: the corpus was expanded and rebalanced, and the calendar and sky engines exist and are calibrated against the diaries' own eclipse records. Plan remains LOCKED at v3.2, nothing found so far warrants an architecture revision.

**Current Babylonian corpus (2026-08-16, all five ADART volumes):**

| | |
|---|---:|
| tablets scraped | 614 |
| observation units | 14,879 |
| usable | 4,869 |
| usable with a trustworthy date | 3,591 |
| usable, zero `[...]` gaps | 2,288 |
| usable but date unreliable (goal-year texts) | 1,278 |

**Phase 0 counts (revised in v3):** 20-30 raw examples for Roman, Vedic, Maya, Korean; 50-100 for Babylonian. Track usable/ambiguous/reject rate per tradition, this is the actual decision basis for the still-open 3-vs-5 traditions fork (plan.md Section 7).

**The table (full detail in `notes/phase0_results.md`):**

| Tradition | Genre | Candidates | Usable | Ambiguous | Reject | Rate |
|---|---|---:|---:|---:|---:|---:|
| Babylonian | observation | 100 | 31 | 39 | 30 | 31% |
| Korean | observation | - | - | - | - | not yet annotated |
| Roman | omen_interpretation | 27 | 3 | 4 | 20 | 11% |
| Vedic | omen_interpretation | 28 | 6 | 13 | 9 | 21% |
| Maya | prophecy | 26 | 14 | 3 | 9 | 54% |

Do not act on these numbers without reading the notes, three of the four rows mean something other than what the bare figure suggests.

**V1 traditions (genre-tagged, build order):**
- [x] Babylonian: observation. **Gate passed, corpus since expanded and rebalanced.** See the table above. Confirmed as the vertical slice.
- [ ] Korean: observation. Vision-extraction gate passed at 0% field error. Annotation pass still owed.
- [ ] Roman: omen_interpretation. Lowest usable rate (11%), but for a reason that may be an architecture question rather than a corpus problem.
- [ ] Vedic: omen_interpretation. Voice-thinness risk CONFIRMED.
- [ ] Maya: prophecy. Best usable rate, smallest state space (13 katuns total, 9 attested).

---

## Last Session Summary

*(most recent entry on top)*

**2026-08-16, data layer expansion and celestial engine (Phase 1 begins)**
- Decision taken by the user: strengthen the data layer before any model work, but **without** adding new civilizations. Backlog sources stay parked per decision #15.
- **Scraped ADART 5 and 6**, which had been downloaded in the last session and never used. 614 tablets now against 331. Observation units 14,879 against 7,836. Usable 4,869 against 2,010. Zero-gap usable 2,288 against 807.
- **The phenomenon skew is fixed, which was the real reason for doing this.** Moon-star conjunctions were 63% of the clean set, now 31%. Stationary points 6 to 108. Eclipses 7 to 63. First and last appearances 66 to 456. Acronychal risings 0 to 23. A fine-tune on the old distribution would have learned one phenomenon and ignored the rest.
- **Month resolution fixed.** Now seeds from the catalogue's months_recorded and steps forward when a day number drops, rather than only tracking in-text markers. Units ambiguous purely from a missing month went 1,097 to 210.
- **ADART 5 and 6 carry no catalogue year or months at all.** The year is read from the text ("Year 64, king Antiochus") and assumed to be Seleucid. Tagged `year_source: text_assumed_seleucid`, not presented as fact.
- **Built `engine/bab_calendar.py` and `engine/sky.py`.** Calendar converts regnal year + month + day to a Julian Day with an uncertainty and a confidence. Sky gives positions, visibility and semantic events, with separations in both degrees and cubits.
- **Calibrated the calendar against the diaries themselves.** A lunar eclipse can only occur at full moon, so the eclipse records are ground truth. The first rule tried ("equinox falls inside month I") put 22 of 30 records exactly +30 days out, one whole lunation. Correct rule is "Nisannu 1 is the first crescent on or after the equinox". Median offset went +30.25 d to +0.86 d.
- **Validation now: 31/48 (65%) of catalogue-dated eclipse records land within 2 days.** The residual is expected, not error: `to_jd` returns the start of the Babylonian day at sunset and "night of the 14th" happens in the hours after.
- **Goal-year texts do not date correctly and the reason is structural.** A goal-year tablet states the year it was compiled *for*, then quotes observations from earlier cycles, so the stated year does not apply to the observations under it. Text-dated records score 23% against the catalogue-dated 65%, median error a whole month. ADART 6 units are tagged `date_confidence: unreliable`. Content good, dates not.
- **Used DE406 rather than the DE441 named in plan.md.** DE441 part 1 is 1.65 GB and the smaller ancient NAIF kernels have moved. DE406 is 300 MB, covers 3000 BC to 3000 AD, and is far more precise than cubit measurements need. Deliberate, documented in `notes/engine.md`.
- Renamed `engine/calendar.py` to `engine/bab_calendar.py` because it shadowed the stdlib `calendar` module and broke Skyfield's imports.

**2026-08-15, Phase 0 Corpus Viability Sprint (data reconnaissance only, no fine-tuning code, no engine)**
- Repo skeleton built out per CLAUDE.md: `data/raw/<tradition>/`, `data/processed/`, `scripts/`, `engine/`, plus `notes/`.
- **Two of five sources had rotted since the plan was written.** attalus.org/docs/diaries.html turns out to be only an *index*: every translation link points at repository.edition-topoi.org, which resolves but refuses connections; ancient-astronomy.org no longer resolves at all. sacred-texts.com now 403s everything non-browser. Worked around both; details in `notes/SOURCES.md`.
- **Babylonian** via ORACC ADsD instead: 331 tablets, 9,102 translated lines, 7,836 dated observation units. 100 read by hand -> 31 usable / 39 ambiguous / 30 reject. Corpus-wide ~2,000 usable, **807 with zero `[...]` gaps**. Gate needs ≥50. Passes by ~40x.
- Gotcha for future sessions: the ORACC bulk JSON dumps contain Akkadian transliteration but **not** the English translation. English only exists in rendered HTML (`<td class="t1 xtr">`), hence two separate fetch scripts.
- **Roman** 3/27 usable, **Vedic** 6/28, **Maya** 14/26. All annotated by reading every sampled item, not keyword scan.
- **Korean vision-extraction gate PASSED at 0.0% field error** (25/25 rows, 96/96 numeric fields) on a deliberately nasty table. Narrow Halley-only fallback not needed. Korean annotation pass still outstanding: it has no row in the table yet.
- Discovered the clean-triple ">2 sentences" rule breaks on Babylonian (semicolon-joined clauses); applying it literally gave 1.7% usable instead of 31%. Substituted a continuous-run measure and flagged it rather than silently settling it.
- 7 commits, all local. **No GitHub remote is configured, so nothing has been pushed.**

**2026-08-15 (later, same session), prompt-only baseline harness built**
- Decision taken: run the prompt-only baseline (plan.md gate item 7) BEFORE building the celestial engine, since plan.md Section 2 makes fine-tuning conditional on this test failing. Pure resequencing, no architecture change.
- Built 5 hand-crafted OBSERVATION_STATEs from real zero-gap diary entries spanning 5 phenomenon types, a few-shot prompt (3 non-overlapping examples), a multi-backend runner, and a deterministic scorer. See `notes/baseline_gate.md`.
- **Not yet run against a real model**: no runner, no API key, 4 GB GPU on this box. `ollama pull qwen2.5:7b` is the cheapest path.
- Scorer is self-tested: real diary entries score 5/5, deliberately broken outputs 0/5, each caught for the intended reason.
- **Found two holes in the gate criteria as written**, both flagged not silently patched:
  - No genre check. An observation-genre output that invents an omen ("...this portends that the king will fall") passes (a), (b) and (c) as written. Added criterion (d).
  - Only object *names* are checked, not the facts. The non-LLM template control scored **5/5 while dropping the watch, the latitude clause, the month number, earthshine and the direction**: all present in the state. Added criterion (e) for measurements and qualifiers; template correctly drops to 0/5.
- Corrected the Vedic annotation after the new source sweep: celestial pool is ~2.7x larger than sampled (Adh 17 on planetary war is a real miss), but the voice-thinness finding is unchanged. Added Gargiya-jyotisha + Parashara/Adbhuta-Sagara to `discovered_sources_backlog.md` Tier S, and the Hora/Jataka texts + Mahabharata to its false-leads table.

**[DATE PLACEHOLDER], Project kickoff / planning session**
- Full project brainstorm and research completed in prior conversation (not in Claude Code: in Claude chat).
- Extensive corpus research done across ~15+ civilizations to find viable data sources for the fine-tuning corpus.
- Landed on 5 traditions for v1 (Roman, Vedic, Maya, Babylonian, Korean), 5 more queued for v2 (Egyptian, Islamic, Persian/Zoroastrian, Aztec, European medieval).
- Aboriginal Australian explicitly excluded on ethical grounds: do not revisit.
- `plan.md`, `continuity.md`, `CLAUDE.md` created as project scaffolding.
- No code written yet. No data fetched yet.

---

## Next Immediate Steps

**The baseline has been run. Results, all against the same cases:**

| tier | main set | held-out generalization set |
|---|---|---|
| non-LLM template control | 0/5 | 0/4 |
| qwen2.5:7b zero-shot | 0/5 | - |
| qwen2.5:7b few-shot (5) | **5/5** | **4/4** |

Facts are solved by prompting, including on phenomena never shown in the prompt.
What is NOT solved is register: the diaries write "I did not watch" in the first
person and qwen returns "not observed", drops the doubled "became stationary"
construction, and drifts to modern phrasing ("3 fingers in magnitude").

**Immediate next actions, in order:**

1. **Build the stratified training set** from the 2,288 zero-gap usable units, excluding the 1,278 date-unreliable goal-year units and quarantining the 9 evaluation cases. Cap moon-star so it does not dominate; keep every stationary, eclipse and acronychal unit.
2. **Register comparison** against the few-shot control, which is the number a fine-tune has to beat.
3. **QLoRA run on 1.5B**, 2 hour Kaggle cap, modest LoRA rank, per plan.md's ladder. The user has decided to proceed with fine-tuning; the conditions that keep it from being wasted are in the 2026-08-16 session entry.
4. **Korean annotation pass**, still the only tradition without a row in the decision table.
5. Consider Parker and Dubberstein's chronology tables to replace the computed year start and settle intercalation. Highest-value single addition to the calendar layer.

**Two user decisions are needed, these are blocking, don't guess at them:**

1. **Does the Roman path have to go through the celestial engine?** Roman scores 11% usable measured as "astronomically conditionable" and roughly 100% measured as "dated + prodigy + interpretation". That single answer moves Roman from the worst tradition to the best, and it decides whether Roman gets cut. plan.md Section 2's diagram implies yes, but it was never stated as a decision.
2. **Is the clean-triple ">2 sentences" rule meant at tablet level or observation-unit level?** They give incompatible answers (1.7% vs 31% usable on Babylonian). All current numbers use the unit-level reading, since plan.md Section 2 defines a training example that way. Confirm or correct.

**Then, in order:**

3. **Run the Korean annotation pass.** It's the only tradition without a row in the decision table, it shares the observation genre with Babylonian, and its extraction risk is now retired. The 3-vs-5 fork should not be settled until Korean has a number.
4. **Re-check the Phase 0 -> Phase 1 gate checklist** in plan.md Section 7 line by line. Item 1 (≥50 clean Babylonian observation units) is comfortably met; the rest concern the engine and schema and are untouched: this session was reconnaissance only, as instructed.
5. Once the gate passes: start the **Babylonian vertical slice** (plan.md Section 7, Phase 1): clean (handling the `[...]` gaps; start from the 807 zero-gap units and hold the 509 fragmentary usable ones out of the first run) -> celestial engine (two-layer + calendar normalization; regnal years and intercalary XII2 months are already visible in the data, so the `alignment` confidence field is needed from the start) -> guardrail wiring -> three-tier baseline -> evaluation suite.
6. **Write the Maya katun sanity-check script** (plan.md Section 4) before any Maya ML work. Phase 0 made this more urgent: 13 total states, 9 attested prophecies.
7. **Set up a GitHub remote** if you want the 7 local commits pushed: none exists yet.
8. Do NOT start fine-tuning before the Babylonian slice validates the pipeline. Do NOT initiate another planning/stress-test round: nothing in Phase 0 justifies one.

---

## Key Decisions Log

*(append-only, do not delete or silently edit past entries; if a decision changes, add a new entry noting the change and why)*

1. Architecture: deterministic astronomy engine (Skyfield/DE441) + small fine-tuned LLM (1-3B, QLoRA). Facts are templated/injected, never freely generated by the model.
2. Hardware: Kaggle free GPU for training, local GTX 1650 4GB for dev/testing only.
3. Copyright posture: personal non-commercial research: not currently a blocker for any source. Revisit if scope changes to public/commercial release.
4. V1 traditions locked: Roman, Vedic, Maya, Babylonian, Korean (priority order = ease of fetch × corpus size).
5. Korean data comes from harvesting astronomy-history academic papers, NOT scraping the primary Sillok site directly (site is only ~11% English-translated as of research date).
6. Aboriginal Australian excluded on ethical (ICIP) grounds: permanent exclusion, not a "couldn't find data" issue.
7. Workflow order is strict: Data Fetch -> Clean/Schema -> Astronomy Engine -> Fine-Tune. No phase-skipping.
8. **UI removed from current scope entirely**: project is data + training only for now. UI will be a separate, later, unplanned phase. Don't build anything UI-related unless explicitly asked.
9. **Model size corrected upward.** Training happens on Kaggle (30 GPU-hrs/week, P100 16GB or T4x2 32GB), not the local 4GB laptop: that affords 7B, 13B models via QLoRA, not just 1-3B. Strategy: 1-3B for fast dev-loop/pipeline testing, 7B, 13B for the real fine-tune once data/schema validated. See plan.md Section 2.
10. **Source audit performed**: found Vietnamese chronicle (Đại Việt Sử Ký Toàn Thư) had been discussed but never added to plan.md; fixed, now in V2 backlog. Final sweep checked CCAG (Byzantine Greek astrology compendium, huge but untranslated + genre-mismatch risk, not pursued) and Book of Enoch Astronomical Book (translated but confirmed no-omen-content, correctly excluded). Source list in plan.md Sections 4/5/6 considered complete as of this audit.
11. **MAJOR PLAN REVISION**: three external LLM stress-tests (ChatGPT, Kimi, Gemini) independently identified the same core flaw: the single "sky state -> diary" schema only genuinely fits Babylonian (and Korean). Roman dates by year not night, Vedic is a rulebook not a log, Maya runs on katun cycles not Gregorian dates. **Resolved by replacing the single schema with three genre types**: observation (Babylonian, Korean), omen_interpretation (Roman, Vedic), prophecy (Maya). Also changed workflow to **vertical-slice-first**: build Babylonian completely through all phases before touching the other four traditions, instead of validating all five before fine-tuning anything. See `plan.md` Section 0 for full detail, and Section 9 for one still-open fork (keep all 5 traditions vs. cut to 3, deferred until after the Babylonian vertical slice). `plan.md` pre-revision version archived as `plan_v1_archive.md` for reference. This is the biggest structural change to the project since kickoff, read plan.md Section 0 fully before doing any further work.
12. **SECOND ROUND OF EXTERNAL STRESS-TEST INCORPORATED (plan v3).** Two more LLM reviews, both converging on "architecture is sound now, stop planning, start Phase 0." Refinements folded in: guardrail split into hard-facts-vs-interpretation (was too blunt before: couldn't distinguish invented facts from legitimate interpretation), celestial engine now explicitly two-layer (physical state + semantic event detector) plus a first-class Calendar Normalization Layer, visibility modeling moved into V1 scope (was missing entirely), "one training example" now explicitly defined as one observation/event not one source text (real corpus sizes are bigger than previously stated), concrete Phase 0 decision rule for the 3-vs-5 fork (usable/ambiguous/reject rate table, not a vibe call), and concrete implementation paths for Maya (GMT correlation constant 584283) and Korean extraction (vision-model on PDF screenshots, not OCR). Previous version archived as `plan_v2_archive.md`. **Both reviewers explicitly said further architecture stress-testing has diminishing returns past this point, next action is Phase 0 execution, not another planning round.**
13. **THIRD ROUND OF EXTERNAL STRESS-TEST INCORPORATED (plan v3.1, patch not full revision).** Six total independent LLM reviews across three rounds now, all converging on "start Phase 0." **Note: this round-3 review was performed against plan v2, not v3**: its praise for the "FACTS-block guardrail" refers to the pre-v3 mechanism, already superseded by v3's hard-facts-vs-interpretation split (OBSERVATION_STATE). That one point of praise is stale; everything else in the review is about the underlying source material (not the schema version) and remains independently valid regardless of which plan version prompted it. Substance incorporated: sharpened Babylonian clean-triple gate (recoverable date + specific observation + >2 sentences of continuous text; if count <~60, pivot vertical slice to Korean instead of forcing Babylonian); fine-tuning made explicitly conditional on the prompting/few-shot baseline failing evaluation checks, not an assumed default; Vedic flagged as having a real voice-thinness risk (legalistic rules, not narrative, may need a lookup-table-plus-light-rendering fallback instead of full generative treatment); Maya flagged for a katun-repetition UX problem (day-granularity slider returns the same prophecy for ~19.7 years at a time, write a standalone no-ML sanity-check script before any fine-tuning work to confirm the interaction actually feels interesting); Korean fallback sharpened (narrow to one well-documented phenomenon, e.g. Halley's Comet only, if PDF extraction proves as bad as feared); evaluation section got an honesty note about the blind-test ceiling (auto-checkable tests are the real evidence, human-judged tradition/style tests are softer signal); synthetic-data bootstrap capped at ~30% of any tradition's set if used. Previous version archived as `plan_v3_archive.md`. **This should be the last planning pass, do not initiate a fourth stress-test round without real Phase 0 data motivating it.**
14. **PLAN LOCKED (v3.2).** Fourth and final round of external stress-test incorporated: 2 more LLM reviews, correctly performed against v3.1 this time (terminology matches exactly), bringing the total to 8 independent reviews across 4 rounds, all converging on the same instruction. This round was pure tactical sharpening, no architecture change: added an explicit frozen research question (plan.md Section 1.5, success is now defined independent of which traditions survive or whether fine-tuning ends up needed at all, so scope pressure can't quietly redefine what "success" means later); demoted LLM-as-judge to secondary evidence behind a deterministic whitelist and a hand-built 30-50 case adversarial test set (avoid "model A judged by model B" as primary scientific evidence); added a concrete Babylonian calendar-complexity caveat (regnal years + king lists + irregular intercalation mean some dates only resolve to a confidence-scored range, not an exact day, use the existing `alignment` block for this, don't hide the uncertainty); sharpened the Babylonian clean-triple gate's fallback into two explicit options rather than a vague "pivot"; added a real cost/testing gate for the Korean vision-extraction approach ($20-50 budget, test on one table before committing, switch to narrow fallback if >30% field-error rate); made the prompt-only baseline pass/fail criterion concrete and testable (5 hand-crafted cases, specific pass conditions, 4/5 threshold); added uncertainty qualifiers (`confidence` field) to the OBSERVATION_STATE schema itself, not just the provenance block; added a practical Kaggle tip (cap first training runs at ~2 hours, not the full 12, to avoid burning quota on a buggy run). Previous version archived as `plan_v3.1_archive.md`. **No further stress-testing rounds are planned. The plan is locked. Next action is Phase 0 execution, if a future session or a new external review proposes another architecture change without real Phase 0 data behind it, that's a signal to be skeptical of the review, not to revise the plan again.**
15. **Discovered-sources backlog created (`discovered_sources_backlog.md`), plan.md NOT touched.** A post-lock sweep (3 more LLM reviews, run specifically to check for missed corpora) surfaced real, sizeable sources beyond the locked V1/V2 scope: most notably China (a much larger source family than the already-excluded Kaiyuan Zhanjing, the 1988 General Compilation of Chinese Ancient Astronomical Records and the Twenty-Four Histories' astronomical treatises), the Neo-Assyrian Astrological Reports (letters combining observation + omen + political advice, arguably the closest match found to the project's original "voice" ambition, already on ORACC), Maya Codices (Dresden/Madrid, a potential fix for the katun-repetition problem, via actual Venus/eclipse/Mars tables), and Irish Annals/CELT (the easiest fetch found in any round, already TEI-tagged with astronomical events pre-identified). All three reviews independently gave the same instruction: don't unlock the plan or expand V1 on this basis. Followed that instruction, created a separate reference-only backlog file instead of editing plan.md. **Consult `discovered_sources_backlog.md` only after Phase 1 succeeds, when deciding Phase 2+ additions, and only with real Phase-0-style viability data for the specific candidate, not before.**

15. **PHASE 0 EXECUTED (2026-08-15).** First session with real data rather than planning. Results in `notes/phase0_results.md`; per-item verdicts in `data/processed/annotation_<tradition>.json`. Decisions and findings recorded:
    - **Babylonian confirmed as the vertical slice.** ~2,000 usable observation units against a gate of 50. Neither plan.md Section 4 fallback triggered.
    - **Babylonian source route changed** from Attalus (dead) to ORACC ADsD. Not a plan revision: ORACC was already the other named source in Section 4.
    - **Maya source route changed** from sacred-texts.com (403s everything) to the archive.org mirror of the same Roys 1933 scan. Same text, different host.
    - **Korean vision-extraction approach validated** at 0% field error; the narrow-scope fallback is NOT triggered. Also found Korean has a second extraction problem the plan didn't anticipate: prose appendices, not just tables, which needs an ordinary parser.
    - **Vedic voice-thinness risk CONFIRMED** with evidence. Recommend promoting the lookup-table treatment from fallback to primary plan. Not actioned; user's call.
    - **Maya katun-repetition problem CONFIRMED and larger than described**: 13 total states, 9 attested. Its 54% usable rate must not be read as corpus health.
    - **The a priori prediction that Vedic and Maya would be the cuts is contradicted by data.** Maya scores best of four; Roman scores worst. The empirical gate earned its keep.
    - **Deferred, not decided:** the 3-vs-5 fork. Korean has no row yet, and Roman's number depends on an unanswered architecture question. Settling it now would be settling it on incomplete data.

16. **DATA LAYER EXPANDED, ENGINE BUILT (2026-08-16).** User decision: strengthen the data layer before the model layer, but do not add new civilizations. Consequences recorded: ADART 5 and 6 brought in (they fix the phenomenon skew, which was the actual risk to a fine-tune, not raw volume); month resolution now uses the catalogue plus day-rollover; ADART 5/6 years are read from text as Seleucid and flagged as an assumption; the calendar layer is calibrated against the diaries' own eclipse records rather than against a rule taken on faith, which caught a whole-lunation error; goal-year texts are marked date-unreliable for a structural reason rather than being quietly included; DE406 substituted for DE441 with the reasoning written down. **User has also decided to proceed to fine-tuning** after the data layer work, against my earlier advice to wait; the conditions that keep that run from being wasted (stratified sampling, quarantined eval cases, 1.5B, 2 hour cap, must beat the few-shot control) are recorded in the session entry and should be honoured.

---

## Open Blockers / Questions

*(carry forward from plan.md Section 9, update as resolved)*

- **[NEW, blocking] Is the Roman path required to go through the celestial engine?** Decides whether Roman reads as 11% or ~100% usable, and therefore whether it gets cut.
- **[NEW, blocking] Does the clean-triple ">2 sentences" rule apply at tablet level or observation-unit level?** The two give incompatible answers. Current numbers use unit-level.
- **[NEW] Korean has no usable/ambiguous/reject row yet.** The 3-vs-5 fork can't be honestly resolved until it does.
- **[NEW] No GitHub remote configured.** 7 commits sitting local-only.
- **[RESOLVED] Korean extraction method**: vision approach tested and passed at 0% field error. See `notes/korean_vision_test.md`.
- **[PARTLY RESOLVED] Korean paper harvesting priority list**: two papers pulled and characterised; a full priority list still isn't built.
- Base model choice not yet tested/decided.
- Style-vs-facts templating mechanism not yet concretely designed.
- Maya katun-cycle -> date-slider mapping not yet designed. Phase 0 raised the urgency: write the no-ML sanity-check script before any Maya modelling.
- Eval rubric for "voice fidelity" not yet designed. Phase 0 note: Maya has by far the strongest distinctive register of the four sampled; Vedic has effectively none. If a tradition is needed to demonstrate real stylistic transfer, Maya is the candidate.
- **Guardrail caveat found in Phase 0:** the deterministic planet-name whitelist in plan.md Section 2 will misfire on Roman text, where "Jupiter", "Mars" and "Venus" nearly always mean temples and statues rather than planets. A naive scan reports 41% celestial content where reading gives 18%.

---

## File Map

*(update whenever new files are added to the project)*

- `plan.md`: full project plan, architecture, data sources, phase breakdown. Stable reference doc.
- `continuity.md`: this file. Session-to-session state.
- `CLAUDE.md`: entry-point instructions for Claude Code, read automatically each session.
- `notes/SOURCES.md`: what plan.md Section 4 says vs. what is actually reachable. Read before re-fetching anything.
- `notes/phase0_results.md`: **the Phase 0 deliverable.** Usable/ambiguous/reject table, per-tradition detail, decision-rule analysis, recommendations.
- `notes/korean_vision_test.md`: the vision-extraction gate test and its result.

**Data (raw):**
- `data/raw/babylonian/translations.jsonl`: 331 scraped ORACC tablets, the tracked raw snapshot.
- `data/raw/babylonian/oracc_json/`, `oracc_html/`: 72 MB of bulk downloads, **gitignored**, regenerate with the two fetch scripts.
- `data/raw/babylonian/_index_diaries.html`: the Attalus index, kept as a cross-reference of which diary years have published translations even though its links are dead.
- `data/raw/roman/obsequens.html`, `data/raw/vedic/brihat_samhita_sastri_1946_djvu.txt`, `data/raw/maya/chilam_balam_chumayel_djvu.txt`
- `data/raw/korean/papers/`: two astronomy-history PDFs; `table_shots/`, rendered page PNGs; `vision_extract_table2.json`, the gate-test extraction.

**Data (processed):**
- `data/processed/babylonian_units.json`: 7,836 segmented observation units, each with verdict + reasons.
- `data/processed/roman_entries.json`, `vedic_slokas.json`, `maya_katun_units.json`: parsed source units.
- `data/processed/annotation_{babylonian,roman,vedic,maya}.json`: per-item manual verdicts with reasons. This is the audit trail behind the table.

**Scripts** (all reconnaissance/parsing only, no engine, no training code, as instructed):
- `scripts/fetch_babylonian.py`: ORACC bulk JSON dumps.
- `scripts/fetch_babylonian_translations.py`: scrapes the English, which the dumps omit.
- `scripts/fetch_other_traditions.py`: Roman, Vedic, Maya single-file fetches.
- `scripts/segment_babylonian.py`: splits tablets into observation units and scores the clean-triple gate.
- `scripts/parse_roman.py`, `parse_vedic.py`, `parse_maya.py`: source-specific structure extraction.
- `scripts/render_pdf_pages.py`: PDF page -> PNG for vision extraction (needs `pymupdf`, installed this session).
- `scripts/verify_vision_extract.py`: scores a vision extraction against the PDF text layer.
- `scripts/fetch_ephemeris.py` downloads DE406 into `engine/ephem/` (gitignored, 300 MB).
- `scripts/baseline_prompt.py`, `run_baseline.py`, `score_baseline.py`, `selftest_scorer.py`: the prompt-only baseline harness. See `notes/baseline_gate.md`.

**Engine (built 2026-08-16):**
- `engine/bab_calendar.py`: regnal year + month + day to Julian Day, with uncertainty and confidence. Named bab_calendar so it does not shadow the stdlib `calendar` module, which breaks Skyfield.
- `engine/sky.py`: positions, visibility, semantic events, eclipse conditions, Normal Star table.
- `engine/validate.py`: validates both layers against the diaries' eclipse records. **Run this after any change to either module.**
- `notes/engine.md`: conventions, the calibration story, current validation numbers, and what would improve them.