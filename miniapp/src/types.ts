export type Lang = 'en' | 'fa';
export type CalendarSystem = 'gregorian' | 'jalali' | 'hijri';

export type AccountType =
  | 'cash'
  | 'card'
  | 'bank'
  | 'e_wallet'
  | 'credit'
  | 'investment'
  | 'savings';

export type Me = {
  telegram_id: number;
  username: string | null;
  display_name: string;
  language_code: Lang;
  calendar_system: CalendarSystem;
  timezone: string;
  default_currency: string | null;
  credit_balance: number;
  is_admin: boolean;
  onboarding_completed: boolean;
};

export type CurrencyOption = {
  code: string;
  name: string;
  symbol: string;
  is_crypto: boolean;
};

export type TimezoneOption = { name: string; label: string };

export type AccountTypeOption = { value: AccountType; icon: string };

export type AppConfig = {
  currencies: CurrencyOption[];
  timezones: TimezoneOption[];
  account_types: AccountTypeOption[];
  calendars: CalendarSystem[];
};

export type OnboardingPayload = {
  language_code: Lang;
  calendar_system: CalendarSystem;
  timezone: string;
  default_currency: string;
  first_account: {
    name: string;
    type: AccountType;
    currency: string;
  };
};

export type OnboardingResult = {
  onboarding_completed: boolean;
  credit_balance: number;
  signup_credits_granted: number;
};
