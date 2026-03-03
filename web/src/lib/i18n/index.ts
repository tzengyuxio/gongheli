import ar from './ar';
import de from './de';
import en from './en';
import es from './es';
import fr from './fr';
import ja from './ja';
import ko from './ko';
import ru from './ru';
import zhHans from './zh-Hans';
import zhHant from './zh-Hant';

export type Lang = 'ar' | 'de' | 'en' | 'es' | 'fr' | 'ja' | 'ko' | 'ru' | 'zh-Hans' | 'zh-Hant';

export interface LangConfig {
  code: Lang;
  label: string;
  dir: 'ltr' | 'rtl';
}

export const LANGUAGES: LangConfig[] = [
  { code: 'ar',      label: 'العربية (ar)',      dir: 'rtl' },
  { code: 'de',      label: 'Deutsch (de)',       dir: 'ltr' },
  { code: 'en',      label: 'English (en)',       dir: 'ltr' },
  { code: 'es',      label: 'Español (es)',       dir: 'ltr' },
  { code: 'fr',      label: 'Français (fr)',      dir: 'ltr' },
  { code: 'ja',      label: '日本語 (ja)',         dir: 'ltr' },
  { code: 'ko',      label: '한국어 (ko)',         dir: 'ltr' },
  { code: 'ru',      label: 'Русский (ru)',       dir: 'ltr' },
  { code: 'zh-Hans', label: '简体中文 (zh-Hans)',  dir: 'ltr' },
  { code: 'zh-Hant', label: '繁體中文 (zh-Hant)',  dir: 'ltr' },
];

export const DEFAULT_LANG: Lang = 'zh-Hant';
export const LANG_KEY = 'gonghe-lang';

export const translations: Record<Lang, Record<string, string>> = {
  'ar': ar,
  'de': de,
  'en': en,
  'es': es,
  'fr': fr,
  'ja': ja,
  'ko': ko,
  'ru': ru,
  'zh-Hans': zhHans,
  'zh-Hant': zhHant,
};

const SUPPORTED_CODES = new Set<string>(LANGUAGES.map(l => l.code));

/**
 * Detect the best matching language from browser/OS locale.
 * Returns undefined if no supported language matches.
 */
export function detectLang(): Lang | undefined {
  const candidates = navigator.languages ?? [navigator.language];
  for (const raw of candidates) {
    const tag = raw.trim();
    // Exact match (e.g. "zh-Hant", "ja", "en")
    if (SUPPORTED_CODES.has(tag)) return tag as Lang;
    // Map zh-Hans-* and zh-CN/zh-SG to zh-Hans
    if (/^zh[-_](Hans|CN|SG)/i.test(tag)) return 'zh-Hans';
    // Map zh-Hant-* and zh-TW/zh-HK/zh-MO, or bare "zh" to zh-Hant
    if (/^zh([-_](Hant|TW|HK|MO))?$/i.test(tag)) return 'zh-Hant';
    // Base language match (e.g. "en-US" → "en", "fr-CA" → "fr")
    const base = tag.split('-')[0].toLowerCase();
    if (SUPPORTED_CODES.has(base)) return base as Lang;
  }
  return undefined;
}

/** Get current language from localStorage, falling back to default. */
export function getLang(): Lang {
  return (localStorage.getItem(LANG_KEY) as Lang) ?? DEFAULT_LANG;
}

/** Check if a string is a valid Lang code. */
export function isLang(code: string): code is Lang {
  return SUPPORTED_CODES.has(code);
}

/** Look up a translation key for the given language, falling back to en. */
export function t(key: string, lang: Lang): string {
  const dict = translations[lang];
  if (dict[key] !== undefined) return dict[key];
  return translations['en'][key] ?? key;
}

/** Format a translation string, replacing all {placeholder} occurrences. */
export function fmt(
  key: string,
  lang: Lang,
  vars: Record<string, string | number>,
): string {
  let str = t(key, lang);
  for (const [k, v] of Object.entries(vars)) {
    str = str.replaceAll(`{${k}}`, String(v));
  }
  return str;
}
