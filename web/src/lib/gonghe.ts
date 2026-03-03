/**
 * Gonghe Calendar (共和曆) conversion module.
 *
 * Conversion chain:
 *   Gregorian date  ──►  JDN  ──►  Ziyu Day (ZDN)  ──►  Gonghe date
 *                   ◄──       ◄──                   ◄──
 *
 * Key constants:
 *   JDN_ZD0 = 613271        ZDN 0 corresponds to JDN 613271
 *   ZD_GH_Y1_M1_D1 = 800974  Gonghe year 1, month 1, day 1 = ZDN 800974
 *
 * Leap year rule: year % 4 === 0 AND year % 128 !== 0  (31/128 rule)
 *
 * Month lengths: 30, 31, 30, 31, 30, 31, 30, 31, 30, 31, 30, 31(+1 on leap year)
 */

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const JDN_ZD0 = 613271; // JDN corresponding to ZDN 0 (Ziyu Day 0)
const ZD_GH_Y1_M1_D1 = 800974; // ZDN of Gonghe year 1, month 1, day 1

const LARGE_LEAP_CYCLE = 128 * 365 + 31; // 46751 days = 128 years
const SMALL_LEAP_CYCLE = 4 * 365 + 1; // 1461 days = 4 years

// Epoch offset: ZDN of the day before Gonghe year 1, month 1, day 1.
const ZD_EPOCH = ZD_GH_Y1_M1_D1 - 1; // 800973

// Cumulative days from month 1 up to (but not including) month i+1.
// Index 0 = 0 (before month 1), index 12 = 366 (leap year full year).
const DAYS_OF_MONTHS = [0, 30, 61, 91, 122, 152, 183, 213, 244, 274, 305, 335, 366];

// Cumulative days within a 4-year cycle, indexed by year-within-cycle (0..4).
// The 4th year is always the leap year within its 4-year block.
const DAYS_OF_YEARS = [0, 365, 730, 1095, 1461];

const GAN = '甲乙丙丁戊己庚辛壬癸';
const ZHI = '子丑寅卯辰巳午未申酉戌亥';

// Weekday names: index 0 = Monday (週一), 6 = Sunday (週日).
const WEEKDAY_NAME = ['週一', '週二', '週三', '週四', '週五', '週六', '週日'];

// JDN 11 is the reference 甲子 day (ganzhi index 0).
const GANZHI_JDN_EPOCH = 11;

// ---------------------------------------------------------------------------
// Helper: integer floor division (matches Python's // behavior for negatives)
// ---------------------------------------------------------------------------

function floorDiv(a: number, b: number): number {
  return Math.floor(a / b);
}

function floorMod(a: number, b: number): number {
  return ((a % b) + b) % b;
}

function floorDivMod(a: number, b: number): [number, number] {
  const q = floorDiv(a, b);
  const r = a - q * b;
  return [q, r];
}

// ---------------------------------------------------------------------------
// Gregorian ↔ JDN (proleptic Gregorian calendar, astronomical year numbering)
// ---------------------------------------------------------------------------

export function gregorianToJdn(year: number, month: number, day: number): number {
  const a = floorDiv(14 - month, 12);
  const y = year + 4800 - a;
  const m = month + 12 * a - 3;
  return day + floorDiv(153 * m + 2, 5) + 365 * y + floorDiv(y, 4) - floorDiv(y, 100) + floorDiv(y, 400) - 32045;
}

export function jdnToGregorian(jdn: number): [number, number, number] {
  const a = jdn + 32044;
  const b = floorDiv(4 * a + 3, 146097);
  const c = a - floorDiv(146097 * b, 4);
  const d = floorDiv(4 * c + 3, 1461);
  const e = c - floorDiv(1461 * d, 4);
  const m = floorDiv(5 * e + 2, 153);
  const day = e - floorDiv(153 * m + 2, 5) + 1;
  const month = m + 3 - 12 * floorDiv(m, 10);
  const year = 100 * b + d - 4800 + floorDiv(m, 10);
  return [year, month, day];
}

// ---------------------------------------------------------------------------
// JDN ↔ Ziyu Day Number (ZDN)
// ---------------------------------------------------------------------------

export function jdnToZiyu(jdn: number): number {
  return jdn - JDN_ZD0;
}

export function ziyuToJdn(zd: number): number {
  return zd + JDN_ZD0;
}

// ---------------------------------------------------------------------------
// ZDN ↔ Gonghe date
// ---------------------------------------------------------------------------

export function ziyuToGonghe(zd: number): [number, number, number] {
  let ed = zd - ZD_EPOCH;

  let [large_q, ed1] = floorDivMod(ed - 1, LARGE_LEAP_CYCLE);
  ed = ed1 + 1;
  let yy = large_q * 128;

  let [small_q, ed2] = floorDivMod(ed - 1, SMALL_LEAP_CYCLE);
  ed = ed2 + 1;
  yy += small_q * 4;

  // Determine year within the 4-year cycle via lookup table.
  for (let i = 1; i <= 4; i++) {
    if (ed <= DAYS_OF_YEARS[i]) {
      yy += i;
      ed -= DAYS_OF_YEARS[i - 1];
      break;
    }
  }

  // Determine month via lookup table.
  let mm = 0;
  for (let i = 1; i <= 12; i++) {
    if (ed <= DAYS_OF_MONTHS[i]) {
      mm = i;
      ed -= DAYS_OF_MONTHS[i - 1];
      break;
    }
  }

  return [yy, mm, ed];
}

export function gongheToZiyu(year: number, month: number, day: number): number {
  let days = (year - 1) * 365 + floorDiv(year - 1, 4) - floorDiv(year - 1, 128);
  days += DAYS_OF_MONTHS[month - 1];
  days += day;
  days += ZD_EPOCH;
  return days;
}

// ---------------------------------------------------------------------------
// Gregorian ↔ Gonghe (composite)
// ---------------------------------------------------------------------------

export function gregorianToGonghe(year: number, month: number, day: number): [number, number, number] {
  const jdn = gregorianToJdn(year, month, day);
  const zd = jdnToZiyu(jdn);
  return ziyuToGonghe(zd);
}

export function gongheToGregorian(year: number, month: number, day: number): [number, number, number] {
  const zd = gongheToZiyu(year, month, day);
  const jdn = ziyuToJdn(zd);
  return jdnToGregorian(jdn);
}

// ---------------------------------------------------------------------------
// Auxiliary functions
// ---------------------------------------------------------------------------

export function isLeapYear(year: number): boolean {
  return year % 4 === 0 && year % 128 !== 0;
}

export function daysInMonth(year: number, month: number): number {
  if (month === 12) {
    return isLeapYear(year) ? 31 : 30;
  }
  return DAYS_OF_MONTHS[month] - DAYS_OF_MONTHS[month - 1];
}

export function ganzhiIndex(zd: number): number {
  return floorMod(ziyuToJdn(zd) - GANZHI_JDN_EPOCH, 60);
}

export function ganzhiName(n: number): string {
  return GAN[floorMod(n, 10)] + ZHI[floorMod(n, 12)];
}

export function weekday(zd: number): number {
  return ziyuToJdn(zd) % 7;
}

export function weekdayName(zd: number): string {
  return WEEKDAY_NAME[weekday(zd)];
}

// ---------------------------------------------------------------------------
// Combined date info
// ---------------------------------------------------------------------------

export interface GongheDate {
  year: number;
  month: number;
  day: number;
  zdn: number;
  ganzhiIdx: number;
  ganzhiStr: string;
  weekdayIdx: number;
  weekdayStr: string;
}

export function getGongheDateFromGregorian(year: number, month: number, day: number): GongheDate {
  const jdn = gregorianToJdn(year, month, day);
  const zdn = jdnToZiyu(jdn);
  const [gy, gm, gd] = ziyuToGonghe(zdn);
  const gzIdx = ganzhiIndex(zdn);
  return {
    year: gy,
    month: gm,
    day: gd,
    zdn,
    ganzhiIdx: gzIdx,
    ganzhiStr: ganzhiName(gzIdx),
    weekdayIdx: weekday(zdn),
    weekdayStr: weekdayName(zdn),
  };
}

export function formatGregorianDate(year: number, month: number, day: number): string {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

export function getTodayGonghe(): GongheDate {
  const now = new Date();
  return getGongheDateFromGregorian(now.getFullYear(), now.getMonth() + 1, now.getDate());
}

export function getTodayGregorianString(): string {
  const now = new Date();
  return formatGregorianDate(now.getFullYear(), now.getMonth() + 1, now.getDate());
}
