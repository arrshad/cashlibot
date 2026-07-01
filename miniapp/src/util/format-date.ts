import type { CalendarSystem, Lang } from '@/types';

const CAL_MAP: Record<CalendarSystem, string> = {
  gregorian: 'gregory',
  jalali: 'persian',
  hijri: 'islamic',
};

/**
 * Format an ISO datetime string in the user's locale, timezone, and calendar.
 * Falls back gracefully if the runtime lacks non-Gregorian calendar support.
 */
export function formatDate(
  iso: string,
  lang: Lang,
  calendar: CalendarSystem,
  timezone: string,
  style: 'short' | 'medium' | 'long' = 'medium',
): string {
  const cal = CAL_MAP[calendar] ?? 'gregory';
  const region = lang === 'fa' ? 'fa-IR' : 'en-US';
  const locale = `${region}-u-ca-${cal}`;
  try {
    return new Intl.DateTimeFormat(locale, {
      timeZone: timezone,
      dateStyle: style,
    }).format(new Date(iso));
  } catch {
    // Falls back to Gregorian in the user's locale.
    return new Intl.DateTimeFormat(region, {
      timeZone: timezone,
      dateStyle: style,
    }).format(new Date(iso));
  }
}
