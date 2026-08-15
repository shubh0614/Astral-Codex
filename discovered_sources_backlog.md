# Discovered Sources Backlog

**This file does NOT modify the locked plan (plan.md v3.2). V1 scope is unchanged.**

This is a reference document, not an action item. It exists because a broader sweep (3 independent LLM searches, run after the plan was locked) turned up real corpora that were missed across all four planning rounds, some of them large. Per explicit recommendation from all three searches: **do not unlock the plan or expand V1 scope on the strength of this document alone.** Consult this file only when:
1. Phase 1 (Babylonian vertical slice) has succeeded, and
2. You're deciding what to add during Phase 2 (horizontal scale-out) or beyond, and
3. Real Phase 0-style viability data exists for the candidate (don't skip that step just because a source looks big on paper).

If a future session (yours or Claude Code's) is tempted to reopen `plan.md` because of something in this file, that's a sign to slow down, not speed up.

---

## How to read the tiers

- **Tier S**: genuinely exciting, worth serious Phase-0-style investigation once horizontal scale-out begins.
- **Tier A**: strong candidates, real corpora, real English access, worth investigating after Tier S.
- **Tier B**: interesting, smaller or harder, fine as later additions or flavor material.
- **Confirmed false leads**: large and tempting-looking, but wrong genre for this project. Don't re-investigate these; the reasoning is already settled.

---

## Tier S

### Gārgīya Jyotiṣa / Vṛddha-Gārgīya Saṃhitā (Sanskrit astral-omen tradition)
Added 2026-08-15 after a Vedic-specific sweep (3 more LLM searches). **All three independently named this as the biggest miss in the Vedic column, which is the strongest convergence any source in this file has.**
- A large Sanskrit omen compendium attributed to Garga, organised into 48+ *aṅgas*, with sections on Jupiter's course (*Bṛhaspati-cāra*), Venus (*Śukra-cāra*), comets (*Ketu-mālā*), meteors (*Ulkā-lakṣaṇa*), halos (*Pariveṣa*) and calamity omens (*Rāṣṭrotpāta-lakṣaṇa*). Genre fit is `omen_interpretation` and it is arguably a better fit than Bṛhat Saṃhitā, since it is a dedicated omen treatise rather than an encyclopedia.
- Bṛhat Saṃhitā ch. 11 says Varāhamihira consulted Garga and Parāśara on comets, so Bṛhat Saṃhitā is partly a surviving node of this older tradition rather than a standalone book.
- **Reality check on access, which is where two of the three reviews quietly agree:** there is no clean full public-domain English translation. What exists is scattered academic translations of individual aṅgas: Pingree on Aṅga 6 (Śukracāra, 1987), Kumagai on Aṅga 39 (Rāṣṭrotpāta-lakṣaṇa, 2007-2015), Mitchiner on Aṅga 41 (Yugapurāṇa, 1986), Zysk on Aṅga 48 (2016). Gemini's review explicitly concluded "leave this in the V2 backlog"; ChatGPT rated fit 9.5/10 but corpus cleanliness low. So the *fit* is excellent and the *fetchability* is poor, the opposite profile from Obsequens.
- **If pursued:** Kumagai's Aṅga 39 is the single highest-value target, being the celestial-and-terrestrial-portents-predicting-political-catastrophe chapter. Treat it as one academic-paper harvest, same technique as Korean, not as a corpus fetch.
- **Provenance warning:** do not label this "an ancient Vedic text by Garga". Manuscript tradition is layered across recensions. Use the `alignment` block: `source_basis: reconstructed_from_recensions`, `match_confidence` low.

### Parāśara comet material / Adbhuta-Sāgara (Ballāla Sena, 12th c.)
Same sweep. Parāśara's comet tradition survives mostly as *quotations in later authors*, with modern attempts to reconstruct a *Parāśara Tantra* from them. Adbhuta-Sāgara (critical edition Muralidhar Jha, 1905) organises the older cometary tradition and has a dedicated *Ketu-adbhuta* chapter. Adbhuta-Sāgara was already on the v2 backlog in plan.md; this sweep argues for upgrading its importance.
- **Important classification note that the sweep got right:** Adbhuta-Sāgara compiles inherited rules, it does not record observations of its own period. Tag `genre: omen_interpretation`, `source_basis: inherited_rule_compilation`. Do **not** tag it `observation`.

### China: General Compilation of Chinese Ancient Astronomical Records + Twenty-Four Histories astronomical treatises
**Not the same thing as Kaiyuan Zhanjing** (which stays correctly excluded, no English translation exists). This is a different, much larger source family:
- The Beijing Observatory's 1988 compilation reportedly contains on the order of 1,600 solar eclipses, 1,100 lunar eclipses, 1,000 comets, 400 meteor showers, 300 aurorae, 100 novae/supernovae, and more: compiled from official dynastic histories across ~2,500+ years.
- The dynastic histories themselves (*Han Shu*, *Hou Han Shu*, etc.) have astronomical treatise sections (*tianwen zhi*) partially available in English via Chinese Text Project and academic papers: explicitly framing celestial phenomena as omens tied to imperial political fortune, which is an excellent genre fit.
- **Roadblock:** the 1988 compilation itself is print-only and likely not digitized in English; the dynastic-history treatises need the same "harvest from academic papers" approach already designed for Korean (Section 4 of plan.md): same vision-extraction technique likely applies, same caveats apply (test on one source first).
- **Genre fit:** observation + omen_interpretation, potentially a genre bridge between the two.

### Neo-Assyrian Astrological Reports
Source: *State Archives of Assyria, Vol. 8* (Hunger, 1992), but also digitized/lemmatized on **ORACC** (same platform already used for Babylonian ADsD).
- ~700 BCE letters from royal scholars to Assyrian kings (Esarhaddon, Assurbanipal), each combining: an observation, a quoted traditional omen, and political advice: e.g. "We kept watch on the 29th day; we did not see the moon... [omen quoted]... [advice given]."
- **This is the closest match found across all four rounds to the project's original "authentic voice" ambition**: it's not a diary and not a rulebook, it's a real document that does both observation and interpretation in one breath.
- **Roadblock:** the modern English translation (Hunger 1992) is in copyright: fine for personal use, but the ORACC digitization is CC-licensed and may only cover transliteration, same pattern as Babylonian ADsD.
- **Genre fit:** could be its own genre variant, or folded into Babylonian as a related but distinct sub-tradition (same civilization lineage, different period/genre).

### Maya Codices (Dresden, Madrid): as a supplement to, not replacement for, Chilam Balam
- Directly addresses the katun-repetition problem flagged in the locked plan (Section 4). The Dresden Codex specifically contains Venus tables, eclipse tables, and a Mars table tied to Long Count dates: actual astronomical content, not just katun-level prophecy.
- A searchable Maya codices database with translation/analysis reportedly exists.
- **Roadblock:** the material is glyphic: interpretation and translation are genuinely difficult, and the surviving corpus is small (nowhere near China's scale). This is a quality/alignment win, not a volume win.
- **Genre fit:** could become a second Maya path alongside Chilam Balam's prophecy genre: an actual observation-adjacent genre for Maya, addressing the exact structural weakness already identified.

### Irish Annals (CELT: Annals of Ulster, Inisfallen, Chronicon Scotorum)
- Spans ~442-1133 CE, documented eclipses, comets, aurorae, volcanic dust events, possibly the 1054 supernova.
- **The single easiest fetch of anything in this entire backlog**: CELT (University College Cork) publishes plain-text/TEI-XML with astronomical/meteorological events already tagged as a term category. This is a genuinely rare case of a historical corpus already being computationally structured for exactly this kind of extraction.
- **Genre fit:** observation / omen_interpretation: entries are brief, dated, often eschatological in tone.

---

## Tier A

### Japan: Nihon Tenmon Shiryo (Kanda, 1935) + Meigetsuki (Fujiwara no Teika's diary, 1180,1235)
- A dedicated multi-volume Japanese historical-astronomical-record compilation (eclipses, comets, meteors, aurorae, occultations, planetary conjunctions), records beginning ~620 CE.
- **Meigetsuki is worth calling out specifically**: it's an actual personal diary containing real sky observations, which is closer to the project's original "diary" concept than almost anything else found in any round.
- **Roadblock:** same academic-compilation-extraction problem as Korean: likely needs the same harvesting approach, same caveats (test on one source first, budget for extraction pain).

### Byzantine chronicles (Theophanes Confessor, Chronicon Paschale, George Synkellos)
- Modern full English translations exist (Mango & Scott for Theophanes; Whitby & Whitby for Chronicon Paschale, Liverpool University Press): genuinely accessible, not a translation project.
- Dated, located (Constantinople, Antioch, etc.) eclipse records with explicit omen framing tied to imperial politics.
- **Genre fit:** observation, similar register to Roman Obsequens but distinct voice.

### Russian/Slavic chronicles (Svyatsky compilation, trans. Vyssotsky, ~1949)
- The Primary Chronicle and successors, systematically mined for astronomical content by Svyatsky; English translation of the compiled astronomical entries exists.
- Vivid, apocalyptic register: "There was a sign in the west, a great star with rays like blood... this portended the invasion of the Polovtsi."
- **Roadblock (real, distinct from other sources):** Russian chronicles date from "Creation of the World" (5508 BCE) or Julian calendar: the Calendar Normalization Layer (plan.md Section 2) will need real work here, more than most other traditions.

### Anglo-Saxon Chronicle: re-flagged as easier than previously scoped
- The locked plan's European medieval entry (Section 5) focused on MGH and called European sources "highest assembly effort of the five" v2-backlog traditions. That undersells the ASC specifically: it's **one continuous, already-English, public-domain document** (Wikisource/Gutenberg), not a multi-chronicle assembly problem.
- ~40 astronomical/atmospheric entries over ~600 years: smaller than Korean or China, but trivial to fetch and fully coherent as one source.
- **Correction to make if this gets promoted:** treat ASC as its own easy-fetch v2 candidate, separate from the harder "assemble many European chronicles" framing currently in plan.md Section 5.

### Islamic eclipse/comet compendia (via Stephenson's *Historical Eclipses and Earth's Rotation*, 1997)
- A modern astrophysicist's curated, English-translated dataset of medieval Islamic eclipse/comet observations, extracted specifically from narrative chronicles (Ibn al-Athir and others).
- **Real risk flagged (echoes the Vedic voice-thinness concern already in the locked plan):** because Stephenson extracted this data for Earth-rotation research, the translations may be stripped of period prose register, reading more like a modern spreadsheet than a medieval scholar. Check this specifically before investing: same "voice thinness" pattern to watch for as with Vedic.

---

## Tier B

### Syriac Chronicle of Zūqnīn (through 775/776 CE)
- Small but exceptional quality: contemporary eyewitness descriptions of aurorae, comets, meteor showers, solar eclipses, and reportedly ten actual drawings of celestial phenomena in the surviving manuscript.
- Not a volume play: a quality/uniqueness play. Good candidate for a "flavor" tradition or a cross-cultural comparison case (see the "phenomenon corpora" idea below) rather than a primary training pillar.

### Welsh Annals (Annales Cambriae)
- Multiple recensions (A: E), ~445-1288 CE, similar profile to Irish Annals but smaller (~18+ testable entries). English translations on Wikisource/historyfiles.co.uk.

### Indian eclipse inscriptions + Mughal chronicles (beyond Brihat Samhita)
- India's historical astronomical record isn't confined to Sanskrit astronomical treatises: inscriptional eclipse records exist (~195 counted in one compilation, 440-1817 CE), and Mughal-era chronicles (e.g. Abu'l Fazl's *Akbarnama*) contain firsthand-ish comet/eclipse descriptions (the 1577 comet, for instance).
- Genuinely expands the Vedic tradition's material if voice-thinness (already flagged in the locked plan) turns out to be a real problem: this gives Vedic an observation-adjacent supplement, not just omen rules.

### MUL.APIN (Babylonian, pre-8th century BCE)
- The most widely copied astronomical text in ancient Mesopotamia: mostly computational (star lists, planetary phases, intercalation rules) but with a short celestial-omen section. Modern English translation exists (Hunger & Steele, Routledge 2018).
- Not really a corpus in the same sense as the others: one coherent compendium. Possibly more useful for informing the semantic event detector layer (plan.md Section 2) than as training text.

### Tibetan eclipse manuscript
- One specific manuscript with 36 eclipse prediction/observation records (1544-1616), already the subject of computational reconstruction research. Small but interesting: good "benchmark" candidate (compare historical calculation vs. modern astronomy) rather than a training-volume source.

---

## Confirmed false leads: don't re-investigate

| Source | Why it looks big | Why it's wrong for this project |
|---|---|---|
| Surya Siddhanta / Panchasiddhantika | Major Sanskrit astronomical texts, translated | Computational - planetary models, trigonometry. Same exclusion bucket as Aratus (plan.md Section 6). |
| Ptolemy's Almagest | Foundational, fully translated (Toomer) | Mathematical/star-catalog, not narrative observation or omen. |
| CDLI (Cuneiform Digital Library) | 320,000+ catalogued texts | Overwhelmingly administrative/legal/literary - astronomical texts are a tiny fraction, not a bulk source. |
| NASA ADS historical scans | Thousands of volumes | Modern scientific astronomy, not historical omen literature - wrong domain entirely. |
| Ethiopian/Ge'ez manuscripts | Real astronomical/astrological manuscripts exist | Interesting manuscript ecosystem, not a clean corpus - same conclusion as the locked plan already reached (Section 6). |
| Southeast Asia (Cambodia, Thailand, Nepal, Sri Lanka inscriptions) | Real records exist | Small scattered clusters, not enough volume to justify inclusion ahead of the Tier S/A candidates above. |
| Bṛhat Jātaka, Laghujātaka, Sāravalī, Bṛhat Parāśara Horā Śāstra, Garga Horā, Yavana Jātaka | Large, well-translated, easy to find, and superficially "Vedic astronomy" | **Hora/Jātaka genre - natal astrology.** Birth chart -> individual fate, not sky event -> collective omen. Structurally incompatible with the schema. Same exclusion logic as Aratus. Flagged here specifically because these are the easiest Sanskrit astrology texts to stumble into and the volume is tempting. |
| Bṛhat Saṃhitā ch. 102-106 (and similar later chapters) | Score high on any celestial-keyword scan | **Measured 2026-08-15: these are Hora material inside Bṛhat Saṃhitā itself.** Adh 104 is 43 slokas of "the Moon in the 5th brings humiliation" - house-transit personal fortune. A celestial-vocabulary regex rates it 84% celestial; it is the wrong genre. The Hora/Samhita guard has to be applied *within* Bṛhat Saṃhitā, not only between texts. |
| Mahābhārata (Bhīṣma/Udyoga Parva celestial portents) | ~150 astronomical references; vivid apocalyptic omen sequence; public-domain Ganguli translation | Genuinely rich *voice*, but undatable - the war's date is an unresolved archaeoastronomical dispute spanning ~2,000 years - and the passages are epic-narrative, not omen-prescriptive. Two of the three searches proposed it specifically as a *style* injection to fix Vedic voice-thinness. Tempting, but injecting undated literary material to fix a voice problem is how a grounded-generation project quietly turns into a style-transfer project. If ever used: `source_basis: literary astronomical passage`, `astronomical_match: inferred`, low confidence, and capped under the 30% synthetic/soft-source ceiling already in plan.md Section 9. |
| Atharvaveda / Ṛgveda celestial references | Oldest layer, historically fascinating | Interpretation of *ketu*/*dhūmaketu* passages as literal comet observations is actively debated in the literature. Historical importance high, clean training data very low. Context, not corpus. |

---

## One structural idea worth remembering (not a v1/v2 concern)

One of the three searches raised something genuinely interesting for later: instead of only organizing data by **civilization -> corpus**, some events were independently recorded by *multiple* traditions, the same comet appearing in Chinese, Korean, Japanese, Babylonian, and Syriac records, for instance. That opens a possible future research thread, **cross-cultural event alignment**: given one real celestial event, compare how the fine-tuned model (or the historical sources themselves) render it in different traditions' voices. This is a legitimate, interesting direction, but it's a v3+ idea, not something to design around now. Noting it here so it isn't lost.

---

*This file is a reference, not a task list. Nothing here is scheduled. Return to it only after Phase 1 succeeds.*
