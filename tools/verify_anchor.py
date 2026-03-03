"""
Verify the astronomical anchor for Gonghe year 1, month 1, day 1.

Hypothesis: Gonghe Y1M1D1 = JDN 1,414,245 corresponds to the December solstice
of astronomical year -841 (842 BC).

Expected result: Skyfield solstice JDN ≈ 1,414,245
"""

from skyfield.api import Loader
from skyfield import almanac

EPH_DIR = '~/.skyfield-data'
TARGET_JDN = 1_414_245
SEARCH_T0_JD = 1_413_500.0  # ~2 years before expected solstice
SEARCH_T1_JD = 1_415_000.0  # ~2 years after expected solstice


def main():
    loader = Loader(EPH_DIR)
    eph = loader('de422.bsp')
    ts = loader.timescale()

    print(f'Searching for December solstices between JD {SEARCH_T0_JD} and {SEARCH_T1_JD}...')
    print(f'Target JDN: {TARGET_JDN}')
    print()

    t0 = ts.tt_jd(SEARCH_T0_JD)
    t1 = ts.tt_jd(SEARCH_T1_JD)
    times, events = almanac.find_discrete(t0, t1, almanac.seasons(eph))

    print('All solstices/equinoxes in search range:')
    season_names = ['March equinox', 'June solstice', 'September equinox', 'December solstice']
    for t, e in zip(times, events):
        jde = t.tt
        jdn = round(jde)
        diff = jdn - TARGET_JDN
        marker = ' <-- TARGET' if e == 3 and abs(diff) <= 2 else ''
        print(f'  {season_names[e]}: JDE={jde:.4f}, JDN≈{jdn}, diff={diff:+d}{marker}')

    print()
    print('--- Verification Result ---')
    dec_solstices = [(t, round(t.tt)) for t, e in zip(times, events) if e == 3]
    for t, jdn in dec_solstices:
        diff = jdn - TARGET_JDN
        print(f'December solstice: JDE={t.tt:.6f}, JDN={jdn}, diff={diff:+d}')
        if diff == 0:
            print('CONFIRMED: JDN matches exactly. Gonghe Y1M1D1 anchor is verified.')
        elif abs(diff) == 1:
            print(f'CLOSE: Off by 1 day (within Meeus approximation error). Anchor is acceptable.')
        else:
            print(f'MISMATCH: Difference is {diff} days. Please review the anchor derivation.')


if __name__ == '__main__':
    main()
