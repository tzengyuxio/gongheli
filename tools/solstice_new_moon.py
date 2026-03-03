#!/usr/bin/env python3
"""
solstice_new_moon.py
====================

Finds dates where the winter solstice, new moon, and ganzhi day 甲子 (index 0)
all coincide — i.e., "朔旦冬至甲子日".

These triple-coincidence dates are the candidates for the anchor of the first
epoch (第一紀) of the Gonghe Calendar.  The historically confirmed anchor is:

  西元 1384年12月13日 (明洪武十七年) — 朔旦冬至甲子日
  Julian Day ≈ 2226911

This script uses the Skyfield library for accurate astronomical calculations.

Ephemeris setup
---------------
Before running, download an ephemeris file with `skyfield`:

    python -c "from skyfield.api import Loader; Loader('~/.skyfield-data').open('de422.bsp')"

Alternatively, run this script with --download to fetch it automatically.

Ephemeris options:
  de422.bsp         : -3000 to 3000 CE, 623 MB   (recommended)
  de441_part-1.bsp  : -13200 to 1969 CE, ~1.6 GB (extended history)

The default ephemeris directory is ~/.skyfield-data.  Use --eph-dir to change it.

Usage:
    python tools/solstice_new_moon.py
    python tools/solstice_new_moon.py --start -900 --end 1400
    python tools/solstice_new_moon.py --start -4000 --end 2000 --ephemeris de441_part-1.bsp
    python tools/solstice_new_moon.py --download
"""

import argparse
import os
from math import floor

from skyfield import almanac
from skyfield.api import Loader


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_EPH_DIR  = os.path.expanduser('~/.skyfield-data')
DEFAULT_EPH_FILE = 'de422.bsp'


# ---------------------------------------------------------------------------
# Astronomical helpers
# ---------------------------------------------------------------------------

def ganzhi_of_jd(jd: float) -> int:
    """
    Return the ganzhi (干支) index of the Julian Day.

    0 = 甲子, 1 = 乙丑, ..., 59 = 癸亥.
    The formula places 甲子 at JD 11.5 (i.e., JDN 12), consistent with
    traditional Chinese calendrical reckoning.
    """
    return (int(floor(jd + 0.5)) - 11) % 60


def is_same_day(t0, t1) -> bool:
    """Return True if two Skyfield Time objects fall on the same calendar day (TT)."""
    y0, m0, d0, *_ = t0.tt_calendar()
    y1, m1, d1, *_ = t1.tt_calendar()
    return (y0, m0, d0) == (y1, m1, d1)


def find_winter_solstice(t0, t1, eph):
    """
    Find the first winter solstice between t0 and t1.

    Skyfield season codes:
      0 = Vernal Equinox   (春分)
      1 = Summer Solstice  (夏至)
      2 = Autumnal Equinox (秋分)
      3 = Winter Solstice  (冬至)
    """
    times, events = almanac.find_discrete(t0, t1, almanac.seasons(eph))
    for event, time in zip(events, times):
        if event == 3:
            return time
    return None


def find_new_moon(t0, t1, eph):
    """
    Find the first new moon between t0 and t1.

    Skyfield moon phase codes:
      0 = New Moon      (新月 / 朔)
      1 = First Quarter (上弦)
      2 = Full Moon     (滿月)
      3 = Last Quarter  (下弦)
    """
    times, events = almanac.find_discrete(t0, t1, almanac.moon_phases(eph))
    for event, time in zip(events, times):
        if event == 0:
            return time
    return None


# ---------------------------------------------------------------------------
# Main search
# ---------------------------------------------------------------------------

def find_solstice_new_moon_jiazi(start_year: int, end_year: int, eph, ts) -> list[dict]:
    """
    Search for dates where winter solstice, new moon, and 甲子 day all coincide.

    For each winter solstice in [start_year, end_year], check whether:
      1. A new moon falls on the same calendar day (within ±1 day window).
      2. The Julian Day of the solstice corresponds to ganzhi index 0 (甲子).

    Returns a list of matching event dicts.
    """
    t_start = ts.utc(start_year, 1, 1)
    t_end   = ts.utc(end_year,  12, 31)

    solstice_times, solstice_events = almanac.find_discrete(
        t_start, t_end, almanac.seasons(eph)
    )

    results = []
    for event, t_sol in zip(solstice_events, solstice_times):
        if event != 3:  # only winter solstices
            continue

        # Search for a new moon within ±1 day of the solstice
        t_nm = find_new_moon(
            ts.tt_jd(t_sol.tt - 1),
            ts.tt_jd(t_sol.tt + 1),
            eph,
        )
        if t_nm is None:
            continue

        # Condition 1: solstice and new moon on the same calendar day
        if not is_same_day(t_sol, t_nm):
            continue

        # Condition 2: ganzhi of the day must be 甲子 (index 0)
        if ganzhi_of_jd(t_sol.tt) != 0:
            continue

        y, m, d, *_ = t_sol.tt_calendar()
        results.append({
            'year':          y,
            'month':         m,
            'day':           d,
            'jd':            t_sol.tt,
            'solstice_utc':  t_sol.utc_iso(),
            'new_moon_utc':  t_nm.utc_iso(),
        })

    return results


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_results(results: list[dict]) -> None:
    """Print matching dates in aligned columns."""
    if not results:
        print("No matching dates found.")
        return
    print(f"{'Date':>12}  {'JD':>14}  {'Solstice (UTC)':>25}  {'New Moon (UTC)':>25}")
    print("-" * 85)
    for r in results:
        date_str = f"{r['year']:>5}/{r['month']:02d}/{r['day']:02d}"
        print(
            f"{date_str:>12}  {r['jd']:>14.4f}"
            f"  {r['solstice_utc']:>25}  {r['new_moon_utc']:>25}"
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find dates where winter solstice, new moon, and 甲子 ganzhi day coincide.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python tools/solstice_new_moon.py\n"
            "  python tools/solstice_new_moon.py --start -900 --end 1400\n"
            "  python tools/solstice_new_moon.py --download\n"
        )
    )
    parser.add_argument(
        '--start', type=int, default=-900,
        help='Start year (default: -900, roughly the Gonghe epoch)'
    )
    parser.add_argument(
        '--end', type=int, default=1400,
        help='End year (default: 1400, covers the first epoch anchor 1384 CE)'
    )
    parser.add_argument(
        '--ephemeris', type=str, default=DEFAULT_EPH_FILE,
        help=f'Ephemeris filename (default: {DEFAULT_EPH_FILE})'
    )
    parser.add_argument(
        '--eph-dir', type=str, default=DEFAULT_EPH_DIR,
        help=f'Directory for ephemeris files (default: {DEFAULT_EPH_DIR})'
    )
    parser.add_argument(
        '--download', action='store_true',
        help='Download the ephemeris file if not already present, then exit'
    )
    args = parser.parse_args()

    loader = Loader(args.eph_dir)

    if args.download:
        print(f"Downloading {args.ephemeris} to {args.eph_dir} ...")
        loader.open(args.ephemeris)
        print("Done.")
        return

    print(f"Loading ephemeris: {args.eph_dir}/{args.ephemeris}")
    eph = loader(args.ephemeris)
    ts  = loader.timescale()

    print(f"Searching {args.start} to {args.end} CE for 朔旦冬至甲子日 ...")
    print()

    results = find_solstice_new_moon_jiazi(args.start, args.end, eph, ts)
    print_results(results)


if __name__ == '__main__':
    main()
