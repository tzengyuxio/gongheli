"""
Gonghe Calendar (共和曆) conversion module.

Conversion chain:
    Gregorian date  ──►  JDN  ──►  Ziyu Day (ZDN)  ──►  Gonghe date
                    ◄──       ◄──                   ◄──

Key constants:
    JDN_ZD0 = 613271        ZDN 0 corresponds to JDN 613271
    ZD_GH_Y1_M1_D1 = 800974  Gonghe year 1, month 1, day 1 = ZDN 800974

Leap year rule: year % 4 == 0 AND year % 128 != 0  (31/128 rule)

Month lengths: 30, 31, 30, 31, 30, 31, 30, 31, 30, 31, 30, 31(+1 on leap year)
"""

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JDN_ZD0 = 613271        # JDN corresponding to ZDN 0 (Ziyu Day 0)
# Anchor: December solstice of astronomical year -841 (842 BC Dec 21).
# Verified with Skyfield + de422.bsp: solstice JDE = 1414245.1287 TT,
# which rounds to JDN 1,414,245 — matches exactly (diff = 0 days).
# Derivation: JDN 1,414,245 → ZDN = 1,414,245 - 613,271 = 800,974
ZD_GH_Y1_M1_D1 = 800974  # ZDN of Gonghe year 1, month 1, day 1

_LARGE_LEAP_CYCLE = 128 * 365 + 31   # 46751 days = 128 years
_SMALL_LEAP_CYCLE = 4 * 365 + 1      # 1461 days = 4 years

# Epoch offset: ZDN of the day before Gonghe year 1, month 1, day 1.
# Used to convert between ZDN and the internal 1-based day count.
_ZD_EPOCH = ZD_GH_Y1_M1_D1 - 1  # 800973

# Cumulative days from month 1 up to (but not including) month i+1.
# Index 0 = 0 (before month 1), index 12 = 366 (leap year full year).
_DAYS_OF_MONTHS = [0, 30, 61, 91, 122, 152, 183, 213, 244, 274, 305, 335, 366]

# Cumulative days within a 4-year cycle, indexed by year-within-cycle (0..4).
# The 4th year is always the leap year within its 4-year block.
# Index 4 = 1461 (full 4-year cycle including 1 leap year).
_DAYS_OF_YEARS = [0, 365, 730, 1095, 1461]

_GAN = '甲乙丙丁戊己庚辛壬癸'
_ZHI = '子丑寅卯辰巳午未申酉戌亥'

# Weekday names: index 0 = Monday (週一), 6 = Sunday (週日).
# Anchor: Gonghe year 1, month 1, day 1 = Monday (JDN 1,414,245; 1414245 % 7 == 0).
_WEEKDAY_NAME = ['週一', '週二', '週三', '週四', '週五', '週六', '週日']

# JDN 11 is the reference 甲子 day (ganzhi index 0).
_GANZHI_JDN_EPOCH = 11

# ---------------------------------------------------------------------------
# Gregorian ↔ JDN (proleptic Gregorian calendar, astronomical year numbering)
# ---------------------------------------------------------------------------

def gregorian_to_jdn(year: int, month: int, day: int) -> int:
    """Convert a proleptic Gregorian date to Julian Day Number.

    Uses astronomical year numbering: 1 BC = year 0, 2 BC = year -1, etc.
    """
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def jdn_to_gregorian(jdn: int) -> tuple[int, int, int]:
    """Convert a Julian Day Number to a proleptic Gregorian date.

    Returns (year, month, day) using astronomical year numbering.
    """
    a = jdn + 32044
    b = (4 * a + 3) // 146097
    c = a - (146097 * b) // 4
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = 100 * b + d - 4800 + m // 10
    return year, month, day


# ---------------------------------------------------------------------------
# JDN ↔ Ziyu Day Number (ZDN)
# ---------------------------------------------------------------------------

def jdn_to_ziyu(jdn: int) -> int:
    """Convert JDN to Ziyu Day Number (ZDN)."""
    return jdn - JDN_ZD0


def ziyu_to_jdn(zd: int) -> int:
    """Convert Ziyu Day Number (ZDN) to JDN."""
    return zd + JDN_ZD0


# ---------------------------------------------------------------------------
# ZDN ↔ Gonghe date
# ---------------------------------------------------------------------------

def ziyu_to_gonghe(zd: int) -> tuple[int, int, int]:
    """Convert Ziyu Day Number to Gonghe calendar date (year, month, day).

    Based on zd2tcal_2 from the original kalendaro project.
    Supports dates before Gonghe year 1 (negative years).
    """
    ed = zd - _ZD_EPOCH  # 1-based offset from the Gonghe epoch

    # Decompose into 128-year and 4-year cycles using divmod.
    # divmod on (ed-1) shifts to 0-based so the remainder spans [0, cycle-1],
    # then +1 restores the 1-based range [1, cycle].
    large_q, ed = divmod(ed - 1, _LARGE_LEAP_CYCLE)
    ed += 1
    yy = large_q * 128

    small_q, ed = divmod(ed - 1, _SMALL_LEAP_CYCLE)
    ed += 1
    yy += small_q * 4

    # Determine year within the 4-year cycle via lookup table.
    for i in range(1, 5):
        if ed <= _DAYS_OF_YEARS[i]:
            yy += i
            ed -= _DAYS_OF_YEARS[i - 1]
            break

    # Determine month via lookup table.
    mm = 0
    for i in range(1, 13):
        if ed <= _DAYS_OF_MONTHS[i]:
            mm = i
            ed -= _DAYS_OF_MONTHS[i - 1]
            break

    return yy, mm, ed


def gonghe_to_ziyu(year: int, month: int, day: int) -> int:
    """Convert a Gonghe calendar date to Ziyu Day Number.

    Based on tcal2zd_1 from the original kalendaro project.
    Uses floor division (Python // behaves correctly for negative numbers).
    """
    days = (year - 1) * 365 + (year - 1) // 4 - (year - 1) // 128
    days += _DAYS_OF_MONTHS[month - 1]
    days += day
    days += _ZD_EPOCH
    return days


# ---------------------------------------------------------------------------
# Gregorian ↔ Gonghe (composite)
# ---------------------------------------------------------------------------

def gregorian_to_gonghe(year: int, month: int, day: int) -> tuple[int, int, int]:
    """Convert a Gregorian date to a Gonghe calendar date."""
    jdn = gregorian_to_jdn(year, month, day)
    zd = jdn_to_ziyu(jdn)
    return ziyu_to_gonghe(zd)


def gonghe_to_gregorian(year: int, month: int, day: int) -> tuple[int, int, int]:
    """Convert a Gonghe calendar date to a Gregorian date."""
    zd = gonghe_to_ziyu(year, month, day)
    jdn = ziyu_to_jdn(zd)
    return jdn_to_gregorian(jdn)


# ---------------------------------------------------------------------------
# Auxiliary functions
# ---------------------------------------------------------------------------

def is_leap_year(year: int) -> bool:
    """Return True if the given Gonghe year is a leap year.

    Leap year rule: year % 4 == 0 AND year % 128 != 0  (31/128 rule)
    """
    return year % 4 == 0 and year % 128 != 0


def days_in_month(year: int, month: int) -> int:
    """Return the number of days in a given Gonghe month."""
    if month == 12:
        return 31 if is_leap_year(year) else 30
    return _DAYS_OF_MONTHS[month] - _DAYS_OF_MONTHS[month - 1]


def ganzhi_index(zd: int) -> int:
    """Return the ganzhi (干支) index (0=甲子, 59=癸亥) for a Ziyu Day."""
    return (ziyu_to_jdn(zd) - _GANZHI_JDN_EPOCH) % 60


def ganzhi_name(n: int) -> str:
    """Return the ganzhi (干支) name string for index n."""
    return _GAN[n % 10] + _ZHI[n % 12]


def weekday(zd: int) -> int:
    """Return the day of the week for a Ziyu Day (0=Monday, 6=Sunday).

    Anchor: Gonghe year 1, month 1, day 1 (ZDN 800974) = Monday (0).
    """
    return ziyu_to_jdn(zd) % 7


def weekday_name(zd: int) -> str:
    """Return the Chinese weekday name (週一..週日) for a Ziyu Day."""
    return _WEEKDAY_NAME[weekday(zd)]
