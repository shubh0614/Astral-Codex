"""
Download the JPL ephemeris the celestial engine needs.

plan.md names DE441. DE441 part 1 is 1.65 GB and the NAIF copies of the smaller
ancient-capable kernels have moved. DE406 covers -3000 to +3000 in 300 MB, which
spans the whole diary range (652 BC to 61 BC) with far more precision than
Babylonian cubit-and-finger measurements require. Recorded as a deliberate
substitution in notes/, not a silent one.

Stored under engine/ephem/, which is gitignored.
"""

import sys
import urllib.request
from pathlib import Path

DEST = Path(__file__).resolve().parents[1] / "engine" / "ephem"
URL = "https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de406.bsp"
NAME = "de406.bsp"


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    out = DEST / NAME
    if out.exists() and out.stat().st_size > 3e8:
        print(f"already have {out} ({out.stat().st_size:,} bytes)")
        return

    def hook(block, size, total):
        if total > 0 and block % 400 == 0:
            pct = block * size / total * 100
            sys.stdout.write(f"\r  {pct:5.1f}%  {block*size/1e6:7.1f} MB")
            sys.stdout.flush()

    print(f"downloading {URL}")
    urllib.request.urlretrieve(URL, out, reporthook=hook)
    print(f"\nsaved {out} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
