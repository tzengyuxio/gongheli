# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gonghe Calendar (共和曆) — a solar calendar system using the first year of the Gonghe regency (841 BC) as its epoch. The project contains a core date conversion library (Python + TypeScript) and a promotional website.

## Key Domain Concepts

- **Conversion chain**: `Gregorian ↔ JDN ↔ ZDN (Ziyu Day) ↔ Gonghe date`
- **Leap rule**: `Y % 4 == 0 AND Y % 128 != 0` (31/128 rule)
- **Month lengths**: odd months = 30 days, even months = 31 days, month 12 = 30 (normal) / 31 (leap). Leap day is at year-end.
- **ZDN 0** corresponds to JDN 613,271. Gonghe year 1, month 1, day 1 = ZDN 800,974.
- **Week anchor**: Gonghe 1/1/1 = Monday. Monday is the first day of the week.

## Architecture

Two parallel implementations of the same conversion logic must stay in sync:

| Implementation | Path | Purpose |
|---|---|---|
| Python | `src/gonghe.py` | Core library, canonical reference |
| TypeScript | `web/src/lib/gonghe.ts` | Web frontend (superset: adds `GongheDate` interface, `getTodayGonghe()`) |

Research tools in `tools/` are standalone Python scripts (not part of the library).

The website (`web/`) is an Astro static site with i18n support (10 languages in `web/src/lib/i18n/`).

## Commands

### Python tests

```bash
cd /Users/user/works/gongheli && .venv/bin/python -m pytest tests/
```

Run a single test:
```bash
.venv/bin/python -m pytest tests/test_gonghe.py::TestZiyuGonghe::test_roundtrip_positive
```

### Web dev server

```bash
cd /Users/user/works/gongheli/web && npm run dev
```

### Web build (static site for GitHub Pages)

```bash
cd /Users/user/works/gongheli/web && npm run build
```

The site deploys to `https://tzengyuxio.github.io/gongheli/` (configured with `base: '/gongheli'` in `astro.config.mjs`).

## Important Notes

- When modifying conversion logic, update **both** `src/gonghe.py` and `web/src/lib/gonghe.ts` to keep them in sync.
- The Python tests use `sys.path.insert` to import from `src/` — no package installation needed.
- `tools/solstice_new_moon.py` requires a ~623 MB ephemeris file (`de422.bsp`); run with `--download` first.
