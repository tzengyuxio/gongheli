#!/usr/bin/env python3
"""
leap_year.py
============

Finds the optimal leap year rule for the Gonghe Calendar (共和曆).

A leap year rule is expressed as "j leap years in every i-year cycle",
giving an average year length of (365·i + j) / i days.

Algorithm
---------
For each cycle length i from 1 to max_year:
  1. Find the best j (1 ≤ j ≤ i) that minimises
         |avg - TROPICAL_YEAR|,  where avg = (365·i + j) / i
  2. Show the row if it sets a new accuracy record (smallest delta so far),
     or if i is in REFERENCE_CYCLES (historically notable rules for comparison).

Result
------
The best simple rule: 31 leap years in every 128 years
  Expressed as: year Y is a leap year iff  Y % 4 == 0  AND  Y % 128 != 0
  Average year = (128 × 365 + 31) / 128 = 46,751 / 128 ≈ 365.242188 days
  Error: ~0.000002 days → ~400,000 years per day of accumulated drift

Properties of this rule:
  - Simple: only two conditions to check
  - The 128-year exception exceeds a human lifespan; many people will never
    witness it in their lifetime
  - Year 0 is NOT a leap year: 0 % 128 == 0, so the exception applies

Comparison with Gregorian (97/400 rule):
  - Error: ~0.000310 days → ~3,226 years per day of drift
  - ~150× worse accuracy than the 128-year rule
  - More complex: requires three divisibility checks (÷4, ÷100, ÷400)

Astronomical constant (source: 臺北市立天文科學教育館《天文年鑑2017》, p.190):
  Tropical year = 365.242190 days

Usage:
    python tools/leap_year.py
    python tools/leap_year.py --max-years 500 --save-results
"""

import argparse

# ---------------------------------------------------------------------------
# Astronomical constant
# Source: 臺北市立天文科學教育館《天文年鑑2017》, p.190
# ---------------------------------------------------------------------------
TROPICAL_YEAR = 365.242190  # mean tropical year in days

# Historically notable leap year cycles, always shown for comparison:
#   100 → Gregorian base rule (100-year no-leap) — shown as context
#   400 → Gregorian full rule (97 leaps per 400 years)
#   900 → proposed reform (218 leaps per 900 years)
REFERENCE_CYCLES = {100, 400, 900}


# ---------------------------------------------------------------------------
# Core search
# ---------------------------------------------------------------------------

def find_best_leap_rule(max_year: int = 1000) -> list[dict]:
    """
    Search for optimal leap year rules up to cycle length max_year.

    For each cycle length i, find the integer j (leaps per cycle) that
    minimises the deviation of (365·i + j)/i from TROPICAL_YEAR.

    A result is included if:
      - It sets a new record for smallest delta (best accuracy so far), OR
      - i is in REFERENCE_CYCLES (shown for historical comparison)

    Returns a list of result dicts sorted by cycle length (n_years).
    """
    # Tolerance: the error of the basic 4-year rule (365.25 - TROPICAL_YEAR).
    # We only care about rules at least as good as "leap every 4 years".
    tolerance = abs(TROPICAL_YEAR * 4 - round(TROPICAL_YEAR * 4))

    results = []
    best_delta = 1.0  # smallest delta seen so far

    for i in range(1, max_year + 1):
        # Find the best j for this cycle length i
        best_j, best_avg, best_j_delta = 0, 0.0, 1.0
        for j in range(1, i + 1):
            avg   = (i * 365 + j) / i
            delta = abs(avg - TROPICAL_YEAR)
            if delta < min(best_j_delta, tolerance):
                best_j, best_avg, best_j_delta = j, avg, delta

        # Skip cycles that can't beat the basic 4-year tolerance
        if best_j_delta > tolerance:
            continue

        is_reference  = (i in REFERENCE_CYCLES)
        is_new_record = best_j_delta < best_delta

        # Include if new record or reference cycle
        if not is_new_record and not is_reference:
            continue

        days_per_drift = round(1 / best_j_delta) if best_j_delta > 0 else float('inf')

        results.append({
            'n_years':         i,
            'n_leaps':         best_j,
            'avg_year':        best_avg,
            'delta':           best_j_delta,
            'delta_seconds':   round(best_j_delta * 86400, 3),
            'years_per_drift': days_per_drift,
            'is_reference':    is_reference,
            'is_new_record':   is_new_record,
        })

        if is_new_record:
            best_delta = best_j_delta

    return results


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_results(results: list[dict]) -> None:
    """Print the leap year rule candidates."""
    print(f"{'Cycle':>6}  {'Leaps':>5}  {'Avg year':>12}  "
          f"{'Error (days)':>12}  {'Error (sec)':>11}  {'Drift (1 day in N yrs)':>22}")
    print("-" * 80)
    for r in results:
        drift = f"{r['years_per_drift']:>10,}年差一天"
        note  = "  ← 現行格里曆規則" if r['is_reference'] and r['n_years'] == 400 else \
                "  ← 現行格里曆基礎" if r['is_reference'] and r['n_years'] == 100 else \
                "  [歷]"             if r['is_reference'] else ""
        print(
            f"{r['n_years']:>5}年 {r['n_leaps']:>4}閏  "
            f"{r['avg_year']:>12.6f}  "
            f"{r['delta']:>12.6f}  "
            f"{r['delta_seconds']:>10.3f}秒  "
            f"{drift}"
            f"{note}"
        )


def save_results(results: list[dict], path: str) -> None:
    """Save results to a text file."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("Gonghe Calendar — Leap Year Rule Search Results\n")
        f.write("=" * 78 + "\n\n")
        f.write(f"Tropical year = {TROPICAL_YEAR} days\n")
        f.write(f"  Source: 臺北市立天文科學教育館《天文年鑑2017》, p.190\n\n")
        f.write(f"{'Cycle':>6}  {'Leaps':>5}  {'Avg year':>12}  "
                f"{'Error (days)':>12}  {'Error (sec)':>11}  "
                f"{'Drift (1 day in N yrs)':>22}\n")
        f.write("-" * 80 + "\n")
        for r in results:
            drift = f"{r['years_per_drift']:>10,}年差一天"
            note  = "  現行格里曆規則" if r['is_reference'] and r['n_years'] == 400 else \
                    "  現行格里曆基礎" if r['is_reference'] and r['n_years'] == 100 else \
                    "  [歷]"          if r['is_reference'] else ""
            f.write(
                f"{r['n_years']:>5}年 {r['n_leaps']:>4}閏  "
                f"{r['avg_year']:>12.6f}  "
                f"{r['delta']:>12.6f}  "
                f"{r['delta_seconds']:>10.3f}秒  "
                f"{drift}"
                f"{note}\n"
            )

        # Highlight the recommended rule
        best = next((r for r in results if r['n_years'] == 128), None)
        if best:
            f.write("\n" + "=" * 78 + "\n")
            f.write("Recommended leap year rule for the Gonghe Calendar\n")
            f.write("-" * 78 + "\n")
            f.write(
                f"  Rule:    Y % 4 == 0  AND  Y % 128 != 0\n"
                f"  Cycle:   {best['n_years']} years, {best['n_leaps']} leap years\n"
                f"  Avg year: {best['avg_year']:.6f} days "
                f"= {best['n_years'] * 365 + best['n_leaps']}/{best['n_years']}\n"
                f"  Error:   {best['delta']:.6f} days ({best['delta_seconds']} sec)\n"
                f"  Drift:   1 day per ~{best['years_per_drift']:,} years\n\n"
                f"  Note: Year 0 is NOT a leap year (0 % 128 == 0).\n"
                f"  The 128-year exception exceeds a human lifespan;\n"
                f"  many people will never witness it in their lifetime.\n"
            )

    print(f"\nResults saved to: {path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find optimal leap year rules for the Gonghe Calendar"
    )
    parser.add_argument(
        "--max-years", type=int, default=1000,
        help="Maximum cycle length to search (default: 1000)"
    )
    parser.add_argument(
        "--save-results", action="store_true",
        help="Save results to tools/leap_year_results.txt"
    )
    args = parser.parse_args()

    print(f"Searching leap year rules up to {args.max_years}-year cycles...")
    print(f"  Tropical year = {TROPICAL_YEAR} days\n")

    results = find_best_leap_rule(args.max_years)
    print_results(results)

    if args.save_results:
        save_results(results, "tools/leap_year_results.txt")


if __name__ == "__main__":
    main()
