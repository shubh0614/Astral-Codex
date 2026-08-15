# Source availability, checked 2026-08-15 (Phase 0)

What plan.md Section 4 says vs. what is actually reachable today. Recorded here
because two of the five sources have moved or died since the plan was written,
and that is itself a Phase 0 finding.

## Babylonian: CHANGED ROUTE

plan.md says "ORACC ADsD + Attalus.org".

**The Attalus route is dead.** `attalus.org/docs/diaries.html` is alive, but it
is only an *index*, it holds no diary text of its own. All 348 translation
links on it point at `repository.edition-topoi.org` (Berlin Ancient Astronomy
Project). That host resolves to 141.20.159.96 but refuses connections on both
80 and 443. `ancient-astronomy.org`, the project's own site, no longer resolves
at all. Wayback was rate-limiting (HTTP 429) at time of check, so a partial
recovery of the Topoi pages may still be possible later, noted as a fallback,
not pursued, because ORACC turned out to be the better source anyway.

**Used instead: ORACC ADsD**, the other source plan.md already names. This is
the Sachs & Hunger *Astronomical Diaries and Related Texts from Babylonia*
edition, structured and CC BY-SA 3.0.

  | volume  | contents                    | catalogue | texts w/ transliteration |
  |---------|-----------------------------|-----------|--------------------------|
  | adart1  | Diaries 652-262 BC          | 417       | 89                       |
  | adart2  | Diaries 261-165 BC          | 417       | 162                      |
  | adart3  | Diaries 164-61 BC           | 417       | 156                      |
  | adart5  | Lunar and planetary texts   | 106       | 105                      |
  | adart6  | Goal-year texts             | 180       | 180                      |

  (The 417 repeats because all three diary volumes ship the same shared
  catalogue. Distinct diary tablets with actual text = 407.)

**Gotcha worth knowing:** the ORACC bulk JSON dumps at `/json/adsd-*.zip`
contain the Akkadian transliteration and lemmatisation but **not** the English
translation. `index-tra.json` references translation files named
`X102613_project-en` which are simply absent from the zips. The English exists
only in the rendered HTML, inside `<td class="t1 xtr">` cells, one cell per
tablet line. Hence two scripts: `fetch_babylonian.py` for the structured dump,
`fetch_babylonian_translations.py` to scrape the English.

adart5 and adart6 were downloaded but held back from the Phase 0 sample,
they are lunar/planetary and goal-year texts, a different text genre from the
night-by-night diaries, and mixing them would muddy the usable-rate number.

## Roman: as planned

`attalus.org/translate/obsequens.html`, full English Obsequens. Clean HTML,
one `[N]` anchor per year, consuls and a `{ NNN B.C. }` year on every entry.
Fetched without incident.

## Vedic: as planned

plan.md says "Full 1946/47 translation on archive.org". Located:
`varahamihiras-brihat-samhita-by-v-subrahmanya-sastri`, Panditabhushana V.
Subrahmanya Sastri, 1946. Used the `_djvu.txt` OCR layer (1.46 MB).

## Maya: CHANGED HOST, same text

plan.md points at sacred-texts.com for Roys 1933. **sacred-texts.com now
returns 403 to everything that isn't a real browser**, plain requests, browser
User-Agent, and full browser header sets all refused; Wayback returned 503 on
the same URL. The identical sacred-texts scan of Roys 1933 is mirrored on
archive.org as `book-of-chilam-balam-the-of-chumayel`, public domain (copyright
not renewed), so the text itself was not compromised, only the host.

## Korean: see notes/korean_vision_test.md

Different problem class from the other four: no single canonical source, the
data lives in tables inside academic PDFs. Handled separately per plan.md
Section 4's vision-extraction gate.
