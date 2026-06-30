/**
 * Format a numeric string/Decimal-like value using a CurrencyOption from the
 * server config. Mirrors the backend's CurrencyFormatter so the two views
 * agree.
 */

import type { CurrencyOption } from '@/types';

export function formatMoney(amount: string | number, currency: CurrencyOption): string {
  const n = typeof amount === 'number' ? amount : Number(amount);
  if (!Number.isFinite(n)) return String(amount);

  const negative = n < 0;
  const abs = Math.abs(n);

  // Round/truncate to the currency's decimal places.
  const fixed = abs.toFixed(currency.decimal_places);
  const [wholeRaw, fracRaw = ''] = fixed.split('.');

  const whole = currency.thousands_separator
    ? withThousands(wholeRaw, currency.thousands_separator)
    : wholeRaw;

  const number =
    currency.decimal_places > 0
      ? `${whole}${currency.decimal_separator}${fracRaw}`
      : whole;

  const sign = negative ? '-' : '';

  return currency.symbol_position === 'before'
    ? `${sign}${currency.symbol}${number}`
    : `${sign}${number} ${currency.symbol}`;
}

function withThousands(whole: string, sep: string): string {
  if (whole.length <= 3) return whole;
  const out: string[] = [];
  for (let i = 0; i < whole.length; i++) {
    if (i > 0 && (whole.length - i) % 3 === 0) out.push(sep);
    out.push(whole[i]);
  }
  return out.join('');
}
