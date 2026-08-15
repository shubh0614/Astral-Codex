# data/raw

Unmodified snapshots of whatever was fetched, one directory per tradition.

Rule (CLAUDE.md): store raw text first, never clean-and-discard in one step.
Anything in here should be reproducible from the fetch script in `scripts/` and
should not be hand-edited. Cleaned output goes in `data/processed/`.

- `babylonian/` — Astronomical Diaries, English translation subset (attalus.org)
- `korean/` — astronomy-history academic paper extractions
- `roman/` — Julius Obsequens, Liber Prodigiorum
- `vedic/` — Brihat Samhita
- `maya/` — Books of Chilam Balam (Roys 1933)
