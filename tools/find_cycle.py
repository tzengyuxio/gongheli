#!/usr/bin/env python3
"""
find_cycle.py
=============

Finds the optimal epoch cycle length (一紀) for the Gonghe Calendar (共和曆).

Background
----------
A good calendar cycle is an integer number of days N that simultaneously
completes a near-integer count of multiple natural periods:

    Traditional Chinese hierarchy (後漢書):
        1元 = 3紀 = 4560 years
        1紀 = 20蔀 = 1520 years   (回歸年 + 朔望月 + 平太陽日 的循環)
        1蔀 = 4章 =   76 years
        1章 =       19 years      (Metonic cycle: 235 synodic months ≈ 19 tropical years)

    This script searches for a modernized "紀" that also aligns with the
    sexagenary (干支) day cycle, giving a 4-way alignment:
        回歸年 (tropical year)
        朔望月 (synodic month)
        干支紀日 (60-day ganzhi cycle)
        七曜 (7-day week)

Algorithm (ported from the original ziyu_day.py :: find_cycle())
-----------------------------------------------------------------
For each year count i from 0 to max_year:

  1. Compute total solar days and total lunar days:
         solar_days = i × TROPICAL_YEAR
         lunar_days = j × SYNODIC_MONTH,  where j = round(i × Y/M)

  2. Both cycles must land on the SAME integer day:
         floor(solar_days) == floor(lunar_days)
     (Otherwise skip; the two cycles are misaligned by at least one day.)

  3. The "time part" of each cycle is how far through the final (partial) day
     the cycle has progressed.  We want BOTH to be deep into that last day —
     so that a single additional day brings both cycles back to a clean start:
         time_part = min(frac(solar_days), frac(lunar_days))

  4. A row is printed (shown as a candidate) if:
         time_part > running_max   — new record; update running_max
         OR time_part ≥ 0.916667  — within the last ~2 hours of the day
     Rows in REFERENCE_YEARS are always printed regardless.

  5. A candidate is marked [x] (valid epoch cycle / 一紀) if additionally:
         N = floor(solar_days) + 1  is divisible by 60  (干支)
         AND N is divisible by 7   (七曜)

Result: the smallest valid epoch cycle is N = 1,613,640 days (i = 4418 years).

Astronomical constants (source: 臺北市立天文科學教育館《天文年鑑2017》, same in 2019):
    Tropical year:  365.242190 days  (p.190)
    Synodic month:  29.530589  days  (p.191)

Usage:
    python tools/find_cycle.py                        # search up to 20000 years
    python tools/find_cycle.py --max-years 7000       # original default
    python tools/find_cycle.py --save-results         # save to tools/cycle_results.txt
"""

import argparse
from datetime import timedelta
from math import modf, floor

# ---------------------------------------------------------------------------
# Astronomical constants
# Source: 臺北市立天文科學教育館《天文年鑑2017》, pp.190–191
# (confirmed unchanged in the 2019 edition)
# ---------------------------------------------------------------------------
TROPICAL_YEAR = 365.242190   # mean tropical year in days
SYNODIC_MONTH = 29.530589    # mean synodic month in days

# ---------------------------------------------------------------------------
# Calendar structural periods (exact integers, used to verify divisibility)
# ---------------------------------------------------------------------------
GANZHI_CYCLE = 60   # sexagenary day cycle (干支紀日)
WEEK_CYCLE   = 7    # week length (七曜)

# Year counts corresponding to time units in ancient Chinese (and Western) calendars.
# These are always printed regardless of alignment quality, so the Gonghe Calendar's
# cycle can be compared directly against historical predecessors.
#
#   19   → 章 (Metonic cycle): 235 synodic months ≈ 19 tropical years
#   76   → 蔀 (Callippic cycle): 4 × 章; used in 四分曆
#  391   → 祖沖之《大明曆》閏周: 144 intercalations per 391 years
# 1520   → 後漢書：1紀 = 20蔀 = 1520 years
# 1539   → 三統曆：1統 = 81章 = 1539 years (朔旦冬至同夜半)
# 4560   → 後漢書：1元 = 3紀 = 4560 years
REFERENCE_YEARS = [19, 76, 391, 1520, 1539, 4560]

# Threshold for "close enough to end of day" (22/24 ≈ 0.9167)
# A time_part above this means the cycle ends within the last ~2 hours of
# the final partial day, making one extra day a good approximation.
THRESHOLD_TIME_PART = 22 / 24  # ≈ 0.916667


# ---------------------------------------------------------------------------
# Core search
# ---------------------------------------------------------------------------

def find_cycle(solar_len: float = TROPICAL_YEAR,
               lunar_len: float = SYNODIC_MONTH,
               max_year: int = 20000) -> list[dict]:
    """
    Search for calendar epoch cycles (一紀 candidates) up to max_year years.

    Parameters
    ----------
    solar_len : float
        Length of one tropical year in days.
    lunar_len : float
        Length of one synodic month in days.
    max_year : int
        Maximum year count to search.

    Returns
    -------
    list of dict, each representing a printed row with keys:
        n_years, n_months, n_days,
        solar_days, lunar_days,
        time_part_solar, time_part_lunar,
        div_ganzhi, div_week, is_epoch,
        is_reference, is_record
    """
    results = []
    running_max_time_part = 0.5  # track the best (highest) min time_part seen so far

    for i in range(max_year + 1):
        # Number of synodic months closest to i tropical years
        j = round(i * solar_len / lunar_len)

        # Total elapsed days for each cycle (floating-point)
        solar_days = i * solar_len
        lunar_days = j * lunar_len

        # Split into integer day count and fractional "time of day" part
        # modf(x) → (fractional_part, integer_part)
        time_part_solar, day_part_solar = modf(solar_days)
        time_part_lunar, day_part_lunar = modf(lunar_days)

        is_reference = (i in REFERENCE_YEARS)
        is_record  = False

        if not is_reference:
            # Both cycles must land on the same integer day — otherwise the
            # year and month cycles diverge by at least a full day at this count
            if day_part_solar != day_part_lunar:
                continue

            # Use the more conservative (smaller) time_part as the alignment score:
            # both cycles need to be deep into that final partial day
            time_part = min(time_part_solar, time_part_lunar)

            if time_part > running_max_time_part:
                # New best alignment — always include, update the running maximum
                running_max_time_part = time_part
                is_record = True
            elif time_part < THRESHOLD_TIME_PART:
                # Below both the record and the 22-hour threshold — not interesting
                continue

        # Integer day count for this cycle: floor(solar_days) + 1
        # For non-integer solar_days this equals ceil(solar_days).
        n_days = int(solar_days) + 1

        # Check divisibility by the two exact integer cycles
        div_ganzhi = (n_days % GANZHI_CYCLE == 0)
        div_week   = (n_days % WEEK_CYCLE   == 0)

        # A valid epoch cycle (紀) must satisfy all four alignment conditions
        is_epoch = div_ganzhi and div_week and not is_reference

        results.append({
            'n_years':        i,
            'n_months':       j,
            'n_days':         n_days,
            'solar_days':     solar_days,
            'lunar_days':     lunar_days,
            'time_part_solar': time_part_solar,
            'time_part_lunar': time_part_lunar,
            'div_ganzhi':     div_ganzhi,
            'div_week':       div_week,
            'is_epoch':       is_epoch,
            'is_reference':     is_reference,
            'is_record':      is_record,
        })

    return results


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def _fmt_timepart(frac: float) -> str:
    """Format a fractional day (0–1) as HH:MM:SS."""
    return str(timedelta(days=frac))[:-7]  # drop microseconds


def print_results(results: list[dict]) -> None:
    """Print the candidate table in the same format as the original find_period.txt."""
    header = (
        "回歸年數, 朔望月數, 太陽日數, "
        "年循環最後一日餘時, 月循環最後一日餘時, "
        "合甲子, 合七曜, "
        "年循環太陽日數, 月循環太陽日數"
    )
    print(header)
    for r in results:
        special_mark = " [歷]" if r['is_reference'] else ""
        record_mark  = " [最]" if r['is_record']  else ""
        epoch_mark_g = "x" if r['div_ganzhi'] else " "
        epoch_mark_w = "x" if r['div_week']   else " "
        print(
            "{0:>5}年 {1:>6}月 {2:>8}日 "
            "{3:>08}時(年) {4:>08}時(月) "
            "[{5}] [{6}] "
            "{7:>16.6f} {8:>16.6f}"
            "{9}{10}".format(
                r['n_years'],
                r['n_months'],
                r['n_days'],
                _fmt_timepart(r['time_part_solar']),
                _fmt_timepart(r['time_part_lunar']),
                epoch_mark_g,
                epoch_mark_w,
                r['solar_days'],
                r['lunar_days'],
                special_mark,
                record_mark,
            )
        )


def print_epoch_summary(results: list[dict]) -> None:
    """Print only the valid epoch cycles (紀) with full statistics."""
    epochs = [r for r in results if r['is_epoch']]
    if not epochs:
        print("No valid epoch cycles found.")
        return

    print()
    print("=" * 70)
    print("Valid Epoch Cycles (一紀)")
    print(f"  N % {GANZHI_CYCLE} == 0  (干支紀日)  AND  N % {WEEK_CYCLE} == 0  (七曜)")
    print("=" * 70)
    print(f"  {'Years':>8}  {'Months':>8}  {'Days':>12}  "
          f"{'Ganzhi':>8}  {'Weeks':>8}  "
          f"{'Year res':>10}  {'Month res':>10}")
    print("-" * 70)
    for r in epochs:
        year_res_min  = (1 - r['time_part_solar']) * 24 * 60
        month_res_min = (1 - r['time_part_lunar']) * 24 * 60
        n_ganzhi = r['n_days'] // GANZHI_CYCLE
        n_weeks  = r['n_days'] // WEEK_CYCLE
        print(
            f"  {r['n_years']:>8,}  {r['n_months']:>8,}  {r['n_days']:>12,}  "
            f"{n_ganzhi:>8,}  {n_weeks:>8,}  "
            f"{_fmt_residual_hms(year_res_min):>10}  "
            f"{_fmt_residual_hms(month_res_min):>10}"
        )
    print("=" * 70)

    first = epochs[0]
    n_ganzhi = first['n_days'] // GANZHI_CYCLE
    n_weeks  = first['n_days'] // WEEK_CYCLE
    year_res_min  = (1 - first['time_part_solar']) * 24 * 60
    month_res_min = (1 - first['time_part_lunar']) * 24 * 60
    print()
    print("Smallest valid epoch cycle (一紀):")
    print(f"  {first['n_days']:,} days")
    print(f"  = {first['n_years']:,} tropical years")
    print(f"  = {first['n_months']:,} synodic months")
    print(f"  = {n_ganzhi:,} sexagenary cycles (干支紀日)")
    print(f"  = {n_weeks:,} weeks (七曜)")
    print(f"  Year cycle ends {_fmt_residual_hms(year_res_min)} ({year_res_min:.2f} min) before midnight")
    print(f"  Month cycle ends {_fmt_residual_hms(month_res_min)} ({month_res_min:.2f} min) before midnight")


def _fmt_residual_hms(minutes: float) -> str:
    """Format residual time in minutes as HH:MM:SS."""
    total_seconds = round(abs(minutes) * 60)
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def save_results(results: list[dict], path: str) -> None:
    """Save full results to a text file."""
    epochs = [r for r in results if r['is_epoch']]

    with open(path, "w", encoding="utf-8") as f:
        f.write("Gonghe Calendar — Epoch Cycle Search Results\n")
        f.write("=" * 78 + "\n\n")
        f.write("Astronomical constants\n")
        f.write(f"  Tropical year  Y = {TROPICAL_YEAR} days\n")
        f.write(f"    Source: 臺北市立天文科學教育館《天文年鑑2017》, p.190\n")
        f.write(f"  Synodic month  M = {SYNODIC_MONTH} days\n")
        f.write(f"    Source: 臺北市立天文科學教育館《天文年鑑2017》, p.191\n\n")
        f.write(f"Alignment threshold: time_part ≥ {THRESHOLD_TIME_PART:.6f} "
                f"(= {THRESHOLD_TIME_PART * 24:.0f}/24 hours)\n\n")

        # Candidate table
        f.write("Candidate Table\n")
        f.write("-" * 100 + "\n")
        f.write(
            "回歸年數, 朔望月數, 太陽日數, "
            "年循環最後一日餘時, 月循環最後一日餘時, "
            "合甲子, 合七曜, "
            "年循環太陽日數, 月循環太陽日數\n"
        )
        for r in results:
            epoch_mark_g = "x" if r['div_ganzhi'] else " "
            epoch_mark_w = "x" if r['div_week']   else " "
            f.write(
                "{0:>5}年 {1:>6}月 {2:>8}日 "
                "{3:>08}時(年) {4:>08}時(月) "
                "[{5}] [{6}] "
                "{7:>16.6f} {8:>16.6f}\n".format(
                    r['n_years'], r['n_months'], r['n_days'],
                    _fmt_timepart(r['time_part_solar']),
                    _fmt_timepart(r['time_part_lunar']),
                    epoch_mark_g, epoch_mark_w,
                    r['solar_days'], r['lunar_days'],
                )
            )
        f.write("\n")

        # Valid epoch cycles
        f.write("Valid Epoch Cycles (一紀)\n")
        f.write("-" * 78 + "\n")
        f.write(f"  {'Years':>8}  {'Months':>8}  {'Days':>12}  "
                f"{'Ganzhi':>8}  {'Weeks':>8}  "
                f"{'Year res':>10}  {'Month res':>10}\n")
        for r in epochs:
            n_ganzhi = r['n_days'] // GANZHI_CYCLE
            n_weeks  = r['n_days'] // WEEK_CYCLE
            year_res_min  = (1 - r['time_part_solar']) * 24 * 60
            month_res_min = (1 - r['time_part_lunar']) * 24 * 60
            f.write(
                f"  {r['n_years']:>8,}  {r['n_months']:>8,}  {r['n_days']:>12,}  "
                f"{n_ganzhi:>8,}  {n_weeks:>8,}  "
                f"{_fmt_residual_hms(year_res_min):>10}  "
                f"{_fmt_residual_hms(month_res_min):>10}\n"
            )
        f.write("\n")

        # Conclusion
        if epochs:
            first = epochs[0]
            n_ganzhi = first['n_days'] // GANZHI_CYCLE
            n_weeks  = first['n_days'] // WEEK_CYCLE
            year_res_min  = (1 - first['time_part_solar']) * 24 * 60
            month_res_min = (1 - first['time_part_lunar']) * 24 * 60
            f.write("Conclusion\n")
            f.write("-" * 78 + "\n")
            f.write(
                f"定 {first['n_years']:,} 年為一紀，"
                f"即回歸年、朔望月、太陽日，以及一甲子的最小公倍數。\n"
                f"{first['n_years']:,}年，"
                f"合{first['n_months']:,}月，"
                f"合{first['n_days']:,}日，"
                f"合{n_ganzhi:,}甲子，"
                f"合{n_weeks:,}週。\n\n"
                f"  Year cycle residual:  {_fmt_residual_hms(year_res_min)} "
                f"({year_res_min:.4f} min) before midnight\n"
                f"  Month cycle residual: {_fmt_residual_hms(month_res_min)} "
                f"({month_res_min:.4f} min) before midnight\n"
            )

    print(f"\nResults saved to: {path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find epoch cycle lengths for the Gonghe Calendar"
    )
    parser.add_argument(
        "--max-years", type=int, default=20000,
        help="Maximum year count to search (default: 20000)"
    )
    parser.add_argument(
        "--save-results", action="store_true",
        help="Save full results to tools/cycle_results.txt"
    )
    parser.add_argument(
        "--full-table", action="store_true",
        help="Print the full candidate table (default: epoch summary only)"
    )
    args = parser.parse_args()

    print(f"Searching up to {args.max_years:,} years...")
    print(f"  Tropical year  Y = {TROPICAL_YEAR} days")
    print(f"  Synodic month  M = {SYNODIC_MONTH} days")
    print(f"  Threshold: time_part ≥ {THRESHOLD_TIME_PART:.6f} ({THRESHOLD_TIME_PART*24:.0f}/24 h)")
    print()

    results = find_cycle(max_year=args.max_years)

    if args.full_table:
        print_results(results)

    print_epoch_summary(results)

    if args.save_results:
        save_results(results, "tools/cycle_results.txt")


if __name__ == "__main__":
    main()
