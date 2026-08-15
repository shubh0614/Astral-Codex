# Korean vision-extraction test (Phase 0 gate)

plan.md Section 4 sets a hard gate before committing to the Korean harvest:
test the vision approach on **one** table first, budget $20–50, and if the first
table comes back with >30% field errors, switch immediately to the narrow
single-phenomenon fallback rather than iterating on extraction prompts.

Ran that test. **It passes, and by a wide margin.**

## What was tested

Paper: *Analysis of historical meteor and meteor shower records: Korean,
Chinese and Japanese chronicles* (arXiv astro-ph/0501216), TABLE 2, page 21 —
historical Korean meteor shower records from Samguksagi, Goryeosa,
Joseonwangjosillok and Jeungbomunheonbigo.

Chosen deliberately as a hard case. It has every pathology plan.md warned
about: a three-line stacked header, superscript footnote markers glued to
column names and to individual cells, a `Period` column drawn as merged cells
spanning fifteen rows via a vertical bracket, `–` used for missing month/day,
and ten separate footnotes that change what a value means.

Method: render page to PNG at 200 DPI (`scripts/render_pdf_pages.py`), hand the
image to a vision model, ask for strict JSON. No OCR, no manual copying.

## Result

| metric | value |
|---|---|
| rows extracted | 25 of 25 |
| numeric fields scored | 96 |
| fields matching the PDF text layer | 96 |
| **field error rate** | **0.0%** |
| plan.md abandon threshold | >30% |

Merged `Period` cells were correctly distributed down their rows rather than
left blank or misaligned. Footnote markers were separated from their values
instead of being concatenated into them (`801 10/11 -` with `footnote_marker: 8`,
not `801 10/11 -8`). The footnote legend was captured as a decode table, which
matters because the `A`/`B`/`C` suffixes on estimated dates are the difference
between an observed date and an interpolated one — precisely the
"observed vs. inferred" distinction plan.md flagged as the thing vision models
tend to lose.

Scoring script: `scripts/verify_vision_extract.py`. It scores against the PDF's
embedded text layer, which is usable as ground truth for individual values
while being useless for extraction — the text layer linearises the header into
`Date of / Observation1 / ( Y M D )2 / J D3 / Day4 / ...` and throws away the
column structure entirely. That contrast is the concrete argument for the
vision route over a text-layer parse.

## Cost

Effectively zero for this test. Two page renders and two image reads. The
$20–50 budget in plan.md was scoped for 500+ pages; nothing like that was
needed to clear the gate.

## Second finding, arguably more useful than the gate result

**Not all of this material is in tables.** The other paper pulled,
*Korean Historical Records on Halley's Comet Revisited* (Lee et al., JASS 31(3),
2014), keeps its records in prose appendices, not tables:

> September 3: A comet appeared in the Samtae constellation. Its tail was
> directed to the west and 3 Cheok long (GS, GJ, BG).
>
> September 9: a) A comet appeared during the day (GS, BG). b) A comet and
> Venus appeared during the day (GJ)

That is already a date plus a specific astronomical observation plus a source
attribution, in English, in running text. It needs a plain text parser, not
vision at all, and it is closer to the observation genre than the meteor table
is — the table gives a date and a shower name, this gives an actual described
sky event with direction and tail length.

So the Korean extraction problem is two problems with two different tools:
tabular catalogues (vision, now proven) and prose appendices (ordinary
parsing). The plan only anticipated the first.

## Recommendation

Do not trigger the narrow-scope fallback. The gate passed at 0% against a
deliberately nasty table, so the full harvest is viable on extraction grounds.
Korean was not sampled for a usable/ambiguous/reject rate in this session —
this was the extraction gate only, and the annotation pass still needs doing
before Korean gets a row in the decision table.
