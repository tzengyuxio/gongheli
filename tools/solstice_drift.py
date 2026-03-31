#!/usr/bin/env python3
"""
solstice_drift.py
=================

Analyze the long-term drift of the winter solstice relative to Gonghe
calendar's January 1st.

The Gonghe calendar uses a purely arithmetic leap year rule:
    Y % 4 == 0 AND Y % 128 != 0  (31 leap years per 128-year cycle)

This gives an average year of 365 + 31/128 = 365.2421875 days,
while the mean tropical year is 365.242190 days.

This script tracks the cumulative offset between the calendar year and
the tropical year, computing maximum deviations over various time spans.

Usage:
    python tools/solstice_drift.py
    python tools/solstice_drift.py --years 20000
"""

import argparse
from fractions import Fraction

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TROPICAL_YEAR = 365.242190  # mean tropical year in days

# Calendar average year as exact fraction: (128*365 + 31) / 128 = 46751/128
CAL_YEAR = Fraction(46751, 128)  # 365.2421875 exactly


def is_leap_year(y: int) -> bool:
    """Gonghe leap year rule."""
    return y % 4 == 0 and y % 128 != 0


def calendar_year_length(y: int) -> int:
    """Return 366 for leap year, 365 otherwise."""
    return 366 if is_leap_year(y) else 365


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyze_drift(n_years: int) -> dict:
    """
    Track the cumulative drift of the winter solstice relative to Jan 1.

    Starting from year 1 (where solstice = Jan 1 by definition), compute
    for each subsequent year how many days the astronomical solstice has
    shifted from January 1st.

    Positive drift = solstice falls AFTER Jan 1 (calendar is too short).
    Negative drift = solstice falls BEFORE Jan 1 (calendar is too long).

    Returns a dict with analysis results.
    """
    # Drift = (tropical year length - calendar year length) accumulated
    # Each year:  drift += TROPICAL_YEAR - calendar_year_length(y)
    #
    # Equivalently, drift after N years = N * TROPICAL_YEAR - sum(cal_lengths)

    drift = 0.0  # cumulative drift in days
    max_drift = 0.0
    min_drift = 0.0
    max_drift_year = 1
    min_drift_year = 1

    # Track by 128-year cycle
    cycle_max_drifts = []
    cycle_min_drifts = []
    current_cycle_max = 0.0
    current_cycle_min = 0.0

    # Milestone tracking
    milestones = {}  # year -> drift at key years
    milestone_years = {128, 400, 500, 1000, 2000, 4418, 4419, 5000, 8836, 10000}

    for y in range(1, n_years + 1):
        cal_len = calendar_year_length(y)
        drift += TROPICAL_YEAR - cal_len

        if drift > max_drift:
            max_drift = drift
            max_drift_year = y
        if drift < min_drift:
            min_drift = drift
            min_drift_year = y

        # Track per-cycle extremes
        if drift > current_cycle_max:
            current_cycle_max = drift
        if drift < current_cycle_min:
            current_cycle_min = drift

        # End of 128-year cycle
        if y % 128 == 0:
            cycle_max_drifts.append(current_cycle_max)
            cycle_min_drifts.append(current_cycle_min)
            current_cycle_max = drift
            current_cycle_min = drift

        if y in milestone_years:
            milestones[y] = drift

    # Secular drift rate
    secular_drift_per_year = TROPICAL_YEAR - float(CAL_YEAR)
    secular_drift_per_cycle = secular_drift_per_year * 128
    years_per_day_drift = 1.0 / abs(secular_drift_per_year) if secular_drift_per_year != 0 else float('inf')

    return {
        'n_years': n_years,
        'max_drift': max_drift,
        'max_drift_year': max_drift_year,
        'min_drift': min_drift,
        'min_drift_year': min_drift_year,
        'milestones': milestones,
        'secular_drift_per_year': secular_drift_per_year,
        'secular_drift_per_cycle': secular_drift_per_cycle,
        'years_per_day_drift': years_per_day_drift,
        'cycle_max_drifts': cycle_max_drifts,
        'cycle_min_drifts': cycle_min_drifts,
    }


def analyze_within_cycle():
    """
    Analyze drift within a single 128-year cycle in detail.

    Shows how the solstice wanders year by year within the first cycle.
    """
    drift = 0.0
    max_drift = 0.0
    min_drift = 0.0
    max_year = 0
    min_year = 0
    yearly = []

    for y in range(1, 129):
        cal_len = calendar_year_length(y)
        drift += TROPICAL_YEAR - cal_len
        yearly.append((y, is_leap_year(y), drift))

        if drift > max_drift:
            max_drift = drift
            min_year  # keep
            max_drift = drift
            max_year = y
        if drift < min_drift:
            min_drift = drift
            min_year = y

    return yearly, max_drift, max_year, min_drift, min_year


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_results(results: dict) -> None:
    """Print the drift analysis results."""
    print("=" * 72)
    print("共和曆冬至偏離量分析")
    print("=" * 72)

    print(f"\n回歸年長度:         {TROPICAL_YEAR} 天")
    print(f"共和曆平均年長:     {float(CAL_YEAR):.10f} 天 = {CAL_YEAR}")
    print(f"每年世俗偏移:       {results['secular_drift_per_year']:+.7f} 天")
    print(f"每 128 年週期偏移:  {results['secular_drift_per_cycle']:+.7f} 天")
    print(f"累積 1 天偏移需要:  ~{results['years_per_day_drift']:,.0f} 年")

    print(f"\n--- 在 {results['n_years']:,} 年範圍內的極值 ---")
    print(f"最大正偏移 (冬至落在 1/1 之後): {results['max_drift']:+.4f} 天 "
          f"(第 {results['max_drift_year']} 年)")
    print(f"最大負偏移 (冬至落在 1/1 之前): {results['min_drift']:+.4f} 天 "
          f"(第 {results['min_drift_year']} 年)")
    print(f"總擺幅: {results['max_drift'] - results['min_drift']:.4f} 天")

    print(f"\n--- 關鍵里程碑的累積偏移 ---")
    print(f"{'年份':>10}  {'累積偏移 (天)':>14}  {'累積偏移 (秒)':>14}  備註")
    print("-" * 65)
    notes = {
        128: "1 個閏法週期",
        400: "格里曆 1 週期",
        500: "",
        1000: "",
        2000: "",
        4418: "1 紀 (4418 年)",
        4419: "1 紀 + 1 年",
        5000: "",
        8836: "2 紀",
        10000: "",
    }
    for y in sorted(results['milestones']):
        d = results['milestones'][y]
        s = d * 86400
        note = notes.get(y, "")
        print(f"{y:>10,}  {d:>+14.6f}  {s:>+13.2f}秒  {note}")

    # Per-cycle extremes evolution
    print(f"\n--- 每個 128 年週期結束時的累積偏移 ---")
    print(f"{'週期':>6}  {'年份範圍':>16}  {'週期結束偏移':>14}  {'週期內最大':>12}  {'週期內最小':>12}")
    print("-" * 72)
    n_show = min(10, len(results['cycle_max_drifts']))
    for i in range(n_show):
        y_start = i * 128 + 1
        y_end = (i + 1) * 128
        cycle_end_drift = (i + 1) * results['secular_drift_per_cycle'] * 128 / 128
        # Actually let's compute it properly
        end_drift_approx = results['milestones'].get(y_end, (i+1) * 128 * results['secular_drift_per_year'])
        print(f"{i+1:>6}  {y_start:>7}-{y_end:<7}  "
              f"{end_drift_approx:>+14.6f}  "
              f"{results['cycle_max_drifts'][i]:>+12.6f}  "
              f"{results['cycle_min_drifts'][i]:>+12.6f}")

    # Show last few cycles too
    if len(results['cycle_max_drifts']) > 15:
        print("  ...")
        for i in range(len(results['cycle_max_drifts']) - 3, len(results['cycle_max_drifts'])):
            y_start = i * 128 + 1
            y_end = (i + 1) * 128
            end_drift = (i + 1) * 128 * results['secular_drift_per_year']
            print(f"{i+1:>6}  {y_start:>7}-{y_end:<7}  "
                  f"{end_drift:>+14.6f}  "
                  f"{results['cycle_max_drifts'][i]:>+12.6f}  "
                  f"{results['cycle_min_drifts'][i]:>+12.6f}")


def print_cycle_detail():
    """Print year-by-year drift within one 128-year cycle."""
    yearly, max_d, max_y, min_d, min_y = analyze_within_cycle()

    print(f"\n{'=' * 72}")
    print("首個 128 年週期逐年偏移")
    print("=" * 72)
    print(f"{'年':>4}  {'閏':>2}  {'曆年天數':>8}  {'累積偏移 (天)':>14}")
    print("-" * 40)

    for y, leap, drift in yearly:
        leap_mark = "★" if leap else ""
        print(f"{y:>4}  {leap_mark:>2}  {366 if leap else 365:>8}  {drift:>+14.6f}")

    print(f"\n週期內最大正偏移: {max_d:+.6f} 天 (第 {max_y} 年)")
    print(f"週期內最大負偏移: {min_d:+.6f} 天 (第 {min_y} 年)")
    print(f"週期內總擺幅: {max_d - min_d:.6f} 天")
    print(f"週期結束偏移: {yearly[-1][2]:+.6f} 天 (世俗漂移)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Analyze winter solstice drift in the Gonghe Calendar"
    )
    parser.add_argument(
        "--years", type=int, default=10000,
        help="Number of years to simulate (default: 10000)"
    )
    parser.add_argument(
        "--cycle-detail", action="store_true",
        help="Show year-by-year detail for the first 128-year cycle"
    )
    args = parser.parse_args()

    results = analyze_drift(args.years)
    print_results(results)

    if args.cycle_detail:
        print_cycle_detail()


if __name__ == "__main__":
    main()
