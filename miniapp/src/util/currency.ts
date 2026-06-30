import type { CurrencyOption } from '@/types';

export function getCurrency(
  currencies: CurrencyOption[],
  code: string,
): CurrencyOption | undefined {
  return currencies.find((c) => c.code === code);
}

export function getCurrencyOrFallback(
  currencies: CurrencyOption[],
  code: string,
): CurrencyOption {
  return (
    getCurrency(currencies, code) ?? {
      code,
      name: code,
      symbol: code,
      symbol_position: 'after',
      decimal_places: 2,
      decimal_separator: '.',
      thousands_separator: ',',
      is_crypto: false,
    }
  );
}
