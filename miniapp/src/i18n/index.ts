import en from './en.json';
import fa from './fa.json';
import type { Lang } from '@/types';

const dicts: Record<Lang, Record<string, string>> = { en, fa };

export function t(
  lang: Lang,
  key: string,
  vars?: Record<string, string | number>,
): string {
  let value = dicts[lang]?.[key] ?? dicts.en[key] ?? key;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      value = value.replaceAll(`{${k}}`, String(v));
    }
  }
  return value;
}

export function applyHtmlLang(lang: Lang): void {
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === 'fa' ? 'rtl' : 'ltr';
}
