"""Tests for the gonghe.py core conversion module."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gonghe import (
    gregorian_to_jdn,
    jdn_to_gregorian,
    jdn_to_ziyu,
    ziyu_to_jdn,
    ziyu_to_gonghe,
    gonghe_to_ziyu,
    gregorian_to_gonghe,
    gonghe_to_gregorian,
    is_leap_year,
    days_in_month,
    ganzhi_index,
    ganzhi_name,
    weekday,
    weekday_name,
)


# ---------------------------------------------------------------------------
# Gregorian <-> JDN
# ---------------------------------------------------------------------------

class TestGregorianJdn:
    def test_known_jdn_j2000(self):
        # J2000.0 epoch: 2000-01-01 noon → JDN 2451545
        assert gregorian_to_jdn(2000, 1, 1) == 2451545

    def test_known_jdn_1978_03_04(self):
        # From constants.py: JDN_GCal_1978_03_04 = 2443572
        assert gregorian_to_jdn(1978, 3, 4) == 2443572

    def test_known_jdn_0001_01_01(self):
        # From constants.py: JDN_GCal_0001_01_01 = 1721426
        assert gregorian_to_jdn(1, 1, 1) == 1721426

    def test_roundtrip_positive(self):
        for date in [(2025, 3, 1), (1384, 12, 13), (1, 1, 1)]:
            assert jdn_to_gregorian(gregorian_to_jdn(*date)) == date

    def test_roundtrip_negative_year(self):
        # Year 0 = 1 BC in astronomical numbering
        jdn = gregorian_to_jdn(0, 1, 1)
        assert jdn_to_gregorian(jdn) == (0, 1, 1)

    def test_jdn_to_gregorian_known(self):
        assert jdn_to_gregorian(2451545) == (2000, 1, 1)
        assert jdn_to_gregorian(2443572) == (1978, 3, 4)


# ---------------------------------------------------------------------------
# JDN <-> ZDN
# ---------------------------------------------------------------------------

class TestJdnZiyu:
    def test_zdn_zero(self):
        # JDN_ZD0 = 613271 → ZDN 0
        assert jdn_to_ziyu(613271) == 0

    def test_ziyu_to_jdn_zero(self):
        assert ziyu_to_jdn(0) == 613271

    def test_roundtrip(self):
        for jdn in [613271, 800000, 1414245, 2451545]:
            assert ziyu_to_jdn(jdn_to_ziyu(jdn)) == jdn


# ---------------------------------------------------------------------------
# ZDN <-> Gonghe
# ---------------------------------------------------------------------------

class TestZiyuGonghe:
    def test_gh_year0_month1_day1_to_ziyu(self):
        assert gonghe_to_ziyu(0, 1, 1) == 800609

    def test_gh_year1_month1_day1_to_ziyu(self):
        assert gonghe_to_ziyu(1, 1, 1) == 800974

    def test_ziyu_to_gh_year0(self):
        assert ziyu_to_gonghe(800609) == (0, 1, 1)

    def test_ziyu_to_gh_year1(self):
        assert ziyu_to_gonghe(800974) == (1, 1, 1)

    def test_roundtrip_positive(self):
        for date in [(1, 1, 1), (100, 6, 15), (2864, 1, 1)]:
            zd = gonghe_to_ziyu(*date)
            assert ziyu_to_gonghe(zd) == date

    def test_roundtrip_zero_year(self):
        zd = gonghe_to_ziyu(0, 1, 1)
        assert ziyu_to_gonghe(zd) == (0, 1, 1)

    def test_roundtrip_negative_year(self):
        for date in [(-1, 1, 1), (-128, 1, 1), (-256, 6, 30)]:
            zd = gonghe_to_ziyu(*date)
            assert ziyu_to_gonghe(zd) == date

    def test_last_day_of_year(self):
        # Gonghe year 4 is a leap year → 366 days; last day = month 12, day 31
        assert gonghe_to_ziyu(4, 12, 31) - gonghe_to_ziyu(4, 1, 1) == 365
        # Year 5 is NOT a leap year → last day = month 12, day 30
        assert gonghe_to_ziyu(5, 12, 30) - gonghe_to_ziyu(5, 1, 1) == 364


# ---------------------------------------------------------------------------
# Gregorian <-> Gonghe (composite)
# ---------------------------------------------------------------------------

class TestGregorianGonghe:
    def test_first_day_of_first_period(self):
        # ZDN 1,613,640 = first day of first 紀 = Gregorian 1384/12/13
        # ZDN 1,613,640 → JDN = 1,613,640 + 613,271 = 2,226,911
        # jdn_to_gregorian(2226911)
        year, month, day = jdn_to_gregorian(2226911)
        assert (year, month, day) == (1384, 12, 21)  # from constants comment

    def test_roundtrip_modern(self):
        date = (2026, 3, 3)
        gh = gregorian_to_gonghe(*date)
        assert gonghe_to_gregorian(*gh) == date

    def test_roundtrip_historical(self):
        for date in [(1, 1, 1), (1384, 12, 13), (1978, 3, 4)]:
            gh = gregorian_to_gonghe(*date)
            assert gonghe_to_gregorian(*gh) == date


# ---------------------------------------------------------------------------
# is_leap_year
# ---------------------------------------------------------------------------

class TestIsLeapYear:
    def test_not_leap_divisible_by_128(self):
        assert is_leap_year(0) is False    # 0 % 128 == 0
        assert is_leap_year(128) is False
        assert is_leap_year(256) is False

    def test_leap_divisible_by_4_not_128(self):
        assert is_leap_year(4) is True
        assert is_leap_year(8) is True
        assert is_leap_year(124) is True
        assert is_leap_year(132) is True

    def test_not_leap_not_divisible_by_4(self):
        assert is_leap_year(1) is False
        assert is_leap_year(2) is False
        assert is_leap_year(3) is False
        assert is_leap_year(5) is False

    def test_negative_leap_divisible_by_4_not_128(self):
        assert is_leap_year(-4) is True
        assert is_leap_year(-8) is True
        assert is_leap_year(-124) is True
        assert is_leap_year(-132) is True

    def test_negative_not_leap_divisible_by_128(self):
        assert is_leap_year(-128) is False
        assert is_leap_year(-256) is False

    def test_negative_not_leap_not_divisible_by_4(self):
        assert is_leap_year(-1) is False
        assert is_leap_year(-2) is False
        assert is_leap_year(-3) is False

    def test_negative_leap_year_has_366_days(self):
        # Verify year -4 is actually 366 days long
        start = gonghe_to_ziyu(-4, 1, 1)
        next_start = gonghe_to_ziyu(-3, 1, 1)
        assert next_start - start == 366

    def test_negative_non_leap_128_has_365_days(self):
        # Verify year -128 is not a leap year (365 days)
        start = gonghe_to_ziyu(-128, 1, 1)
        next_start = gonghe_to_ziyu(-127, 1, 1)
        assert next_start - start == 365


# ---------------------------------------------------------------------------
# days_in_month
# ---------------------------------------------------------------------------

class TestDaysInMonth:
    def test_month_1(self):
        assert days_in_month(1, 1) == 30

    def test_month_2(self):
        assert days_in_month(1, 2) == 31

    def test_month_12_normal(self):
        assert days_in_month(1, 12) == 30   # year 1 is not a leap year

    def test_month_12_leap(self):
        assert days_in_month(4, 12) == 31   # year 4 is a leap year

    def test_all_months_sum_normal_year(self):
        total = sum(days_in_month(1, m) for m in range(1, 13))
        assert total == 365

    def test_all_months_sum_leap_year(self):
        total = sum(days_in_month(4, m) for m in range(1, 13))
        assert total == 366


# ---------------------------------------------------------------------------
# ganzhi_index / ganzhi_name
# ---------------------------------------------------------------------------

class TestWeekday:
    def test_year1_month1_day1_is_monday(self):
        # Anchor: Gonghe year 1, month 1, day 1 = Monday (weekday index 0)
        zd = gonghe_to_ziyu(1, 1, 1)
        assert weekday(zd) == 0
        assert weekday_name(zd) == '週一'

    def test_year0_month1_day1_is_sunday(self):
        zd = gonghe_to_ziyu(0, 1, 1)
        assert weekday(zd) == 6
        assert weekday_name(zd) == '週日'

    def test_consecutive_days(self):
        zd = gonghe_to_ziyu(1, 1, 1)
        expected = ['週一', '週二', '週三', '週四', '週五', '週六', '週日', '週一']
        for i, name in enumerate(expected):
            assert weekday_name(zd + i) == name

    def test_weekday_returns_0_to_6(self):
        zd = gonghe_to_ziyu(1, 1, 1)
        for i in range(14):
            assert 0 <= weekday(zd + i) <= 6


class TestGanzhi:
    def test_ganzhi_name_zero(self):
        assert ganzhi_name(0) == '甲子'

    def test_ganzhi_name_59(self):
        assert ganzhi_name(59) == '癸亥'

    def test_ganzhi_name_60_wraps(self):
        assert ganzhi_name(60) == '甲子'

    def test_ganzhi_index_returns_0_to_59(self):
        for zd in range(0, 120):
            idx = ganzhi_index(zd)
            assert 0 <= idx < 60
