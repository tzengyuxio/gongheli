#!/usr/bin/env python3
"""Generate iCalendar (.ics) files with Gonghe Calendar dates.

Usage examples:
    python tools/generate_ics.py --start 2026 --end 2030
    python tools/generate_ics.py --start 2026 --end 2030 --lang en --ganzhi
    python tools/generate_ics.py --start gh2867 --end gh2871 --lang zh --ganzhi
"""

import argparse
import sys
import os
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gonghe import (
    gregorian_to_gonghe,
    gregorian_to_jdn,
    jdn_to_ziyu,
    gonghe_to_gregorian,
    ganzhi_index,
    ganzhi_name,
    weekday,
    is_leap_year,
)

# UID domain for generated events
_UID_DOMAIN = 'gongheli.calendar'


def _parse_year(s: str) -> tuple[str, int]:
    """Parse a year argument. Returns ('gh', year) or ('ce', year)."""
    if s.lower().startswith('gh'):
        return 'gh', int(s[2:])
    return 'ce', int(s)


def _gh_year_to_ce_range(gh_year: int) -> tuple[date, date]:
    """Return the CE date range [start, end) for a Gonghe year."""
    y1, m1, d1 = gonghe_to_gregorian(gh_year, 1, 1)
    days = 366 if is_leap_year(gh_year) else 365
    y2, m2, d2 = gonghe_to_gregorian(gh_year + 1, 1, 1)
    return date(y1, m1, d1), date(y2, m2, d2)


def _format_summary(gh_year: int, gh_month: int, gh_day: int,
                    zdn: int, lang: str, with_ganzhi: bool) -> str:
    """Format the event summary line."""
    if lang == 'zh':
        base = f'共和 {gh_year} 年 {gh_month} 月 {gh_day} 日'
    else:
        base = f'Gonghe {gh_year}-{gh_month:02d}-{gh_day:02d}'

    if with_ganzhi:
        gz = ganzhi_name(ganzhi_index(zdn))
        base += f' {gz}'

    return base


def _ics_escape(text: str) -> str:
    """Escape special characters for iCalendar text values."""
    return text.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,')


_CAL_NAMES = {
    ('zh', False): '共和曆',
    ('zh', True):  '共和曆（干支）',
    ('en', False): 'Gonghe Calendar',
    ('en', True):  'Gonghe Calendar (Ganzhi)',
}


def generate_ics(start_date: date, end_date: date,
                 lang: str, with_ganzhi: bool,
                 cal_name: str | None = None) -> str:
    """Generate iCalendar content for the given CE date range [start, end)."""
    # DTSTAMP: RFC 5545 required field; use file generation time
    dtstamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

    name = cal_name or _CAL_NAMES.get((lang, with_ganzhi), 'Gonghe Calendar')

    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Gonghe Calendar//generate_ics//EN',
        'CALSCALE:GREGORIAN',
        f'X-WR-CALNAME:{name}',
        f'NAME:{name}',
        'METHOD:PUBLISH',
    ]

    current = start_date
    while current < end_date:
        ce_y, ce_m, ce_d = current.year, current.month, current.day
        gh_y, gh_m, gh_d = gregorian_to_gonghe(ce_y, ce_m, ce_d)
        jdn = gregorian_to_jdn(ce_y, ce_m, ce_d)
        zdn = jdn_to_ziyu(jdn)

        summary = _format_summary(gh_y, gh_m, gh_d, zdn, lang, with_ganzhi)
        dt_str = current.strftime('%Y%m%d')
        uid = f'{dt_str}-{lang}-{"gz" if with_ganzhi else "nogz"}@{_UID_DOMAIN}'

        next_day = current + timedelta(days=1)
        dt_end_str = next_day.strftime('%Y%m%d')

        lines.extend([
            'BEGIN:VEVENT',
            f'DTSTAMP:{dtstamp}',
            f'DTSTART;VALUE=DATE:{dt_str}',
            f'DTEND;VALUE=DATE:{dt_end_str}',
            f'SUMMARY:{_ics_escape(summary)}',
            f'UID:{uid}',
            'TRANSP:TRANSPARENT',
            'END:VEVENT',
        ])

        current = next_day

    lines.append('END:VCALENDAR')
    return '\r\n'.join(lines) + '\r\n'


def main():
    parser = argparse.ArgumentParser(
        description='Generate iCalendar (.ics) files with Gonghe Calendar dates.')
    parser.add_argument('--start', required=True,
                        help='Start year: CE year (e.g. 2026) or Gonghe year (e.g. gh2867)')
    parser.add_argument('--end', required=True,
                        help='End year (inclusive): CE year or Gonghe year (e.g. 2030, gh2871)')
    parser.add_argument('--lang', choices=['zh', 'en'], default='zh',
                        help='Language: zh (Chinese) or en (English). Default: zh')
    parser.add_argument('--ganzhi', action='store_true',
                        help='Include ganzhi (干支) in event titles')
    parser.add_argument('-o', '--output',
                        help='Output file path. Default: auto-generated name')
    parser.add_argument('--no-bom', action='store_true',
                        help='Omit UTF-8 BOM (for subscription files; BOM may break Google Calendar subscription)')
    args = parser.parse_args()

    start_kind, start_year = _parse_year(args.start)
    end_kind, end_year = _parse_year(args.end)

    if start_kind != end_kind:
        print('Error: --start and --end must use the same year format '
              '(both CE or both gh).', file=sys.stderr)
        sys.exit(1)

    if start_year > end_year:
        print('Error: --start must be <= --end.', file=sys.stderr)
        sys.exit(1)

    # Determine CE date range
    if start_kind == 'gh':
        start_date = _gh_year_to_ce_range(start_year)[0]
        end_date = _gh_year_to_ce_range(end_year)[1]
        year_label = f'gh{start_year}-gh{end_year}'
    else:
        start_date = date(start_year, 1, 1)
        end_date = date(end_year + 1, 1, 1)
        year_label = f'{start_year}-{end_year}'

    ics_content = generate_ics(start_date, end_date, args.lang, args.ganzhi)

    if args.output:
        out_path = args.output
    else:
        ganzhi_suffix = '_ganzhi' if args.ganzhi else ''
        out_path = f'gonghe_{args.lang}{ganzhi_suffix}_{year_label}.ics'

    with open(out_path, 'wb') as f:
        if not args.no_bom:
            f.write(b'\xef\xbb\xbf')  # UTF-8 BOM (helps Google Calendar import for CJK)
        f.write(ics_content.encode('utf-8'))

    # Count events for summary
    days = (end_date - start_date).days
    print(f'Generated {out_path} ({days} events, {os.path.getsize(out_path) / 1024:.1f} KB)')


if __name__ == '__main__':
    main()
