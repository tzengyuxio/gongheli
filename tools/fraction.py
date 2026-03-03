#!/usr/bin/env python3
"""
fraction.py
===========

Finds the best rational approximations to a floating-point number.

For calendar design this is used to find leap year rules: given a target
value (e.g. the tropical year length 365.242190 days), the tool identifies
fractions p/q that minimise |p/q - target| across increasing denominators q.

Each new entry in the output represents a strictly better approximation than
all previous ones with smaller denominators — i.e. these are the
"convergents" and "best rational approximations" of the continued-fraction
expansion of the target.

Usage:
    # Find best approximations to the tropical year length:
    python tools/fraction.py --value 365.242190 --max-denom 1000

    # Include historically notable denominators for comparison:
    python tools/fraction.py --value 365.242190 --max-denom 10000 --special 128,400,900

    # Find lunisolar intercalation ratio (tropical year / synodic month):
    python tools/fraction.py --value 12.368267 --max-denom 500 --special 19

Example output for --value 0.242190 --max-denom 200:
      1 /   4 | 0.250000000 | delta: + 0.007810000   <-- leap every 4 years
      7 /  29 | 0.241379310 | delta: - 0.000810690
      8 /  33 | 0.242424242 | delta: + 0.000234242
     31 / 128 | 0.242187500 | delta: - 0.000002500   <-- Gonghe Calendar rule
"""

import argparse
from math import floor

# ---------------------------------------------------------------------------
# Astronomical constants
# Source: 臺北市立天文科學教育館《天文年鑑2017》, p.190-191
# ---------------------------------------------------------------------------
TROPICAL_YEAR   = 365.242190   # mean tropical year in days
SYNODIC_MONTH   = 29.530589    # mean synodic month in days
LUNISOLAR_RATIO = TROPICAL_YEAR / SYNODIC_MONTH  # ≈ 12.368267


# ---------------------------------------------------------------------------
# Core algorithm
# ---------------------------------------------------------------------------

def find_fraction(
    value: float,
    max_denominator: int,
    *,
    min_denominator: int = 1,
    special: set[int] | None = None,
) -> list[dict]:
    """
    Find best rational approximations p/q to `value`.

    For each denominator q from min_denominator to max_denominator, find the
    integer p that minimises |p/q - value|.  A result is included if:
      - It sets a new record for smallest delta (strictly better than all
        previous denominators), OR
      - q is in `special` (shown for comparison regardless of accuracy).

    Returns a list of result dicts sorted by denominator.
    """
    if special is None:
        special = set()

    results: list[dict] = []
    best_delta = float('inf')

    for q in range(max(1, min_denominator), max_denominator + 1):
        top       = value * q
        left_int  = floor(top)
        right_int = left_int + 1
        left_d    = top - left_int    # distance to floor
        right_d   = right_int - top  # distance to ceiling

        if left_d <= right_d:
            p, delta = left_int, left_d
        else:
            p, delta = right_int, right_d

        is_special    = q in special
        is_new_record = delta < best_delta

        if not is_new_record and not is_special:
            continue
        if p == 0:
            continue  # skip trivial zero numerator

        approx = p / q
        signed_delta = approx - value

        results.append({
            'numerator':     int(p),
            'denominator':   int(q),
            'approx':        approx,
            'delta':         delta,
            'signed_delta':  signed_delta,
            'is_special':    is_special,
            'is_new_record': is_new_record,
        })

        if is_new_record:
            best_delta = delta

    return results


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_results(results: list[dict], value: float) -> None:
    """Print rational approximation results in aligned columns."""
    print(f"target: {value}")
    print()
    for r in results:
        op    = '+' if r['signed_delta'] >= 0 else '-'
        note  = '  [*]' if r['is_special'] and not r['is_new_record'] else ''
        print(
            f"  {r['numerator']:>6d} / {r['denominator']:>6d}"
            f"  |  {r['approx']:.9f}"
            f"  |  delta: {op} {abs(r['signed_delta']):.9f}"
            f"{note}"
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Find best rational approximations p/q to a target float value.\n"
            "Useful for discovering optimal leap year or intercalation rules."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Preset targets:\n"
            f"  --tropical-year   : {TROPICAL_YEAR} (tropical year in days)\n"
            f"  --synodic-month   : {SYNODIC_MONTH} (synodic month in days)\n"
            f"  --lunisolar-ratio : {LUNISOLAR_RATIO:.6f} (years per lunisolar cycle)\n"
            f"  --leap-fraction   : {TROPICAL_YEAR - 365:.6f} (fractional days per year, for leap rules)\n"
        )
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--value',          type=float, help='Target value to approximate')
    group.add_argument('--tropical-year',  action='store_true', help=f'Use tropical year ({TROPICAL_YEAR})')
    group.add_argument('--synodic-month',  action='store_true', help=f'Use synodic month ({SYNODIC_MONTH})')
    group.add_argument('--lunisolar-ratio', action='store_true', help=f'Use lunisolar ratio ({LUNISOLAR_RATIO:.6f})')
    group.add_argument('--leap-fraction',  action='store_true', help=f'Use leap fraction ({TROPICAL_YEAR - 365:.6f})')

    parser.add_argument(
        '--max-denom', type=int, default=1000,
        help='Maximum denominator to search (default: 1000)'
    )
    parser.add_argument(
        '--min-denom', type=int, default=1,
        help='Minimum denominator to start from (default: 1)'
    )
    parser.add_argument(
        '--special', type=str, default='',
        help='Comma-separated list of denominators to always show (e.g. 19,128,400)'
    )
    args = parser.parse_args()

    # Resolve target value
    if args.tropical_year:
        value = TROPICAL_YEAR
    elif args.synodic_month:
        value = SYNODIC_MONTH
    elif args.lunisolar_ratio:
        value = LUNISOLAR_RATIO
    elif args.leap_fraction:
        value = TROPICAL_YEAR - 365
    else:
        value = args.value

    special = {int(s) for s in args.special.split(',') if s.strip()} if args.special else set()

    results = find_fraction(
        value,
        max_denominator=args.max_denom,
        min_denominator=args.min_denom,
        special=special,
    )
    print_results(results, value)


if __name__ == '__main__':
    main()
