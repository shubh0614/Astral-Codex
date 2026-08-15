# Phase 0: Corpus Viability Sprint: results

Run 2026-08-15. Format follows plan.md Section 7.

## The table

| Tradition | Genre | Candidates | Usable | Ambiguous | Reject | Usable rate |
|---|---|---:|---:|---:|---:|---:|
| Babylonian | observation | 100 | 31 | 39 | 30 | **31%** |
| Korean | observation | 34 | 5 | 26 | 3 | **15%** |
| Roman | omen_interpretation | 27 | 3 | 4 | 20 | **11%** |
| Vedic | omen_interpretation | 28 | 8 | 15 | 5 | **29%** |
| Maya | prophecy | 26 | 14 | 3 | 9 | **54%** |

**All five rows are now filled.** Korean was annotated 2026-08-16
(`annotation_korean.json`). Vedic was re-sampled the same day against a
corrected chapter list (`annotation_vedic_v2.json`), raising it from 21% and
roughly doubling its pool from 254 to 419 slokas.

Every tradition was annotated by reading every sampled item, not by keyword
scan. Per-item verdicts with reasons are in
`data/processed/annotation_<tradition>.json`.

**Read this table with the notes below before acting on it.** Three of the four
rows mean something different from what the number alone suggests.

## Per-tradition detail

### Babylonian: 31% usable, gate passes decisively

331 tablets scraped from ORACC, 9,102 translated lines, segmented into **7,836
dated observation units**. 100 read by hand.

- Corpus-wide classifier: 2,010 usable units (25.7%), agreeing with the hand
  annotation 71/100 with no usable/reject flips.
- **807 usable units contain no `[...]` gap at all.**
- plan.md's gate is ≥50 clean observation units. Measured: roughly 2,000-2,400.
  Passes by a factor of about forty. Neither Section 4 fallback is needed.
- Fragmentary entries flagged separately as instructed: 1,965 units (25%) carry
  three or more gaps; 509 of the usable ones are heavily fragmentary and should
  be held out of a first training run.
- Ceiling is higher than measured: ADART 5 and 6 were excluded as a different
  text genre, 76 catalogued tablets have no digitised text, and ~1,100
  ambiguous units are ambiguous only because my parser failed to resolve their
  month, which a better calendar parse recovers.

### Roman: 11% usable, and this is the surprise

Obsequens parses cleanly into 81 entries, **every one of them dated** by
consulship with an editorial B.C. year. Date is never the constraint. The
constraint is that Roman prodigies are overwhelmingly not astronomical: rains
of blood and stones, deformed births, sweating statues, lightning strikes.

Only 3 of 27 sampled entries carry a sky event the engine could compute (two
solar eclipses and a delayed lunar crescent). A full-corpus read of every
celestial-vocabulary hit across all 81 entries gives 5-6 hard-computable
entries, i.e. about 7%, so the 11% sample figure is real and if anything
generous.

**Two traps found here:**

1. **Planet names are false positives.** "Jupiter", "Mars", "Venus" and
   "Mercury" in Obsequens nearly always mean temples, statues and cult objects.
   "The spears of Mars moved" is the Regia statue. A naive whitelist scan
   reports 41% celestial content where reading gives about 18%. This matters
   directly for the deterministic-whitelist validator in plan.md Section 2,
   that validator would be badly wrong on Roman text.
2. **The number depends on the question.** Measured as "date + any prodigy +
   period-voice interpretation", Obsequens scores essentially 81/81. Measured
   as "astronomically conditionable", it scores 11%. plan.md Section 2 routes
   Roman through the celestial engine, which forces the second reading. If
   Roman were re-scoped to condition on prodigy *type* rather than sky state,
   it would become the healthiest corpus of the four.

### Vedic: 21% usable, voice-thinness confirmed

1,557 slokas extracted from the Sastri 1946 OCR, 254 in the chapters plan.md
names (3-11, 46). 28 read.

- **plan.md Section 4's voice-thinness risk is confirmed.** Every usable sloka
  is a bare conditional: "When Venus is in Hasta, the Kauravas and artists will
  suffer. There will be drought." There is no narrative, no scene, no
  observational register, nothing that constitutes a voice to transfer. The
  longest usable entry is two sentences.
- The 46% ambiguous rate has two very different causes that must not be
  conflated. Five of the 13 ambiguous entries are computable rules damaged only
  by OCR truncation, fixable. The rest key on qualities the engine can never
  supply: the colour of Venus, the shape of the solar disc, the form of
  sunspots, a comet's crest direction. That half will not improve.
- So 21% is a floor on extraction grounds and close to a ceiling on content
  grounds. The computable subset is essentially planet-in-nakshatra, eclipses
  and heliacal risings, much narrower than the chapter list implies.

### Maya: 54% usable, and the number is misleading

Highest usable rate and by far the strongest voice. "Rains from a rabbit sky,
rains from a parched sky, rains from a woodpecker sky" is distinctive and would
be instantly recognisable in a blind evaluation. Rejects are all chronicle
entries and Roys's editorial notes, katun-keyed but not prophecy.

**But the state space is 13.** That is the entire Maya cycle, and only 9 katuns
carry a usable prophecy in Chumayel. plan.md Section 4 flagged this as a slider
UX problem; at the data level it is larger than that. Maya simultaneously has
the best usable rate of the four and the smallest possible conditioning space
of any of them, 13 states against Babylonian's thousands of dated sky states.

A usable/ambiguous/reject table structurally cannot see this, which is exactly
why it is written down here. **Do not read Maya's 54% as corpus health.**

Also confirmed: Maya celestial content is symbolic, not observational. Katun 13
Ahau has the sun eclipsed for five days; Katun 3 Ahau has it moved from its
place for three months. Neither is possible. plan.md Section 2 was right to
route Maya around the astronomy layers entirely.

### Korean: 15% usable, and the constraint is not what the plan assumed

**Annotated 2026-08-16. Full detail in `annotation_korean.json`.**

34 candidates, which is not a sample but everything the two harvested papers
publish at the individual-record level: 9 prose records from the Halley
appendices, 25 rows from the meteor table. 5 usable, 26 ambiguous, 3 reject. On
prose alone it is 5 of 9.

**The number is not the finding.** Extraction was supposed to be the Korean
problem and it is solved: the vision gate passed at 0% field error and the prose
appendices parse with an ordinary regex. The obstacle is that these papers
publish **dates and classifications, not the original entry text**. TABLE 1 of
the meteor paper reports Korea holding 3,861 meteor records, 31 meteor shower
records and 54 meteorites across the three dynasties. What the papers expose as
individual records is 34, and only 9 carry any prose.

A table row gives perfect conditioning facts and nothing to generate. For a
state-to-text task it cannot be a training example however clean the data is.

So harvesting more astronomy-history papers multiplies structured records
without necessarily yielding more target text. The text lives in the chronicles
themselves, and plan.md Key Decision 5 routed around those precisely because the
Sillok is only about 11% English-translated.

**Korean is not blocked on extraction difficulty. It is blocked on whether
English-translated chronicle text can be obtained at volume.** That is a
different question from the one the plan posed, and it should be answered before
Korean is treated as the large-corpus tradition.

Separately, none of the Korean material is engine-drivable today: all 9 prose
records are comet apparitions and the table is meteor showers, neither of which
the current Skyfield and DE406 engine supports. Both are tractable additions.

### Korean: the earlier extraction-gate result

Different problem class, handled per plan.md Section 4's separate gate. Full
write-up in `notes/korean_vision_test.md`.

- Vision extraction tested on one deliberately nasty table (stacked header,
  merged cells spanning 15 rows, superscript footnote markers, dashes for
  missing values): **25/25 rows, 96/96 numeric fields correct, 0.0% field
  error** against a 30% abandon threshold. Cost effectively nil.
- **Do not trigger the narrow Halley-only fallback.** The full harvest is
  viable on extraction grounds.
- Second finding, arguably more useful: not all of this material is tabular.
  The Halley paper keeps its records in *prose* appendices, "September 3: A
  comet appeared in the Samtae constellation. Its tail was directed to the west
  and 3 Cheok long", which needs an ordinary parser, not vision, and is closer
  to the observation genre than the tables are. Korean is two extraction
  problems, not one. The plan anticipated only the first.
- Korean has no usable/ambiguous/reject row yet. It needs an annotation pass
  before it can take part in the 3-vs-5 decision.

## Against plan.md's decision rule

> If a tradition's usable rate collapses (roughly ≤20%) while the others hold
> up well above it, cut that tradition to v2. If all five hold up reasonably
> (even unevenly, e.g. 60-95%), keep all five.

Mechanically applied, with all five rows now filled: **Roman at 11% and Korean
at 15% are the two below the line.** Vedic sits at 29% after re-sampling,
Babylonian at 31%, Maya at 54%. Nobody reaches the 60-95% band the rule
describes as "holding up", so the rule's second branch never fires.

That result inverts the prior twice over. plan.md Section 9 records a reviewer
arguing a priori for cutting **Vedic and Maya**. On real data Maya has the best
usable rate, Vedic came up after correction, and the two below the line are
Roman and Korean, neither of which anyone predicted. Korean in particular was
expected to be the *largest* corpus in the project.

**But the rate is the wrong number for Korean**, and this is the more important
finding. Korean yields 5 usable prose records against Babylonian's 2,288, a
factor of roughly 450. The rate understates how thin it is, because 25 of its 34
candidates are table rows that carry perfect facts and no text at all. See the
Korean section below.

**But do not cut Roman on this number alone**, for two reasons stated above:
the 11% is an artifact of requiring astronomical conditioning, and Roman scores
near-100% on date coverage and interpretive structure. The genuine finding is
narrower and more useful than "cut Roman":

> Roman is a poor fit for *astronomically conditioned* generation and an
> excellent fit for *omen-pattern conditioned* generation. Which it is depends
> on an architecture question plan.md has not explicitly answered.

## Recommendation

Not a decision, this is the user's call, and it interacts with the frozen
research question in plan.md Section 1.5.

1. **Babylonian: proceed to Phase 1.** The gate passes by a wide margin. Start
   from the 807 zero-gap usable units.
2. **Korean: run the annotation pass** before the 3-vs-5 fork is settled. It is
   the only tradition without a row, it shares the observation genre with
   Babylonian, and its extraction risk has now been retired.
3. **Roman: resolve the conditioning question before cutting.** Decide whether
   the Roman path is required to go through the celestial engine. That single
   answer moves Roman between 11% and ~100%.
4. **Vedic: treat the lookup-table fallback as the plan, not the fallback.**
   The rule text is short, formulaic and finite. That is what a lookup table is
   for, and the voice-thinness finding says there is no voice to learn anyway.
5. **Maya: the katun sanity-check script plan.md Section 4 asks for is now
   more urgent, not less.** With 13 total states and 9 attested prophecies,
   write it before any ML work, as instructed.

## Method notes and one thing needing a decision

**The clean-triple "more than two sentences" criterion does not work at the
observation-unit level.** Babylonian diary entries join clauses with semicolons,
so this,

> Night of the 15th, beginning of the night, the moon was 2/3 cubit in front of
> η Piscium; last part of the night, Mars was 3 1/2 cubits below ε Leonis.

, is two complete, independently datable, fully computable observations and
counts as *one* sentence. Applying the criterion literally scored the corpus at
1.7% usable, wrong by roughly fifteen times. Editorial `?` marks push the count
the other way.

Substituted: longest continuous run of text uninterrupted by a `[...]` gap,
minimum 60 characters. This measures what the criterion was reaching for
without depending on punctuation the corpus does not use.

**This is a criterion-definition question, not a data question, so it is
flagged rather than settled.** The >2-sentence rule reads as though written for
tablet-level text, while plan.md Section 2 defines the training example at the
observation-unit level. Those two are in tension. Every number above uses the
unit-level reading, since that is what the architecture consumes.

**Source rot:** two of five sources had moved or died since the plan was
written. Details in `notes/SOURCES.md`. Babylonian went through ORACC instead
of the dead Topoi repository; Maya came from the archive.org mirror because
sacred-texts.com now 403s everything.
