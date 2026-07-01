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
  symbol_position: 'before' | 'after';
  decimal_places: number;
  decimal_separator: string;
  thousands_separator: string;
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

export type Account = {
  id: string;
  name: string;
  type: AccountType;
  currency: string;
  current_balance: string; // decimal serialized as string
  icon: string;
  color: string | null;
  is_default: boolean;
  is_default_income: boolean;
  is_archived: boolean;
  created_at: string;
};

export type AccountCreatePayload = {
  name: string;
  type: AccountType;
  currency: string;
  icon?: string;
  color?: string | null;
  is_default?: boolean;
  is_default_income?: boolean;
};

export type AccountPatchPayload = Partial<{
  name: string;
  icon: string;
  color: string | null;
  is_default: boolean;
  is_default_income: boolean;
}>;

export type CurrencyTotal = {
  currency: string;
  amount: string;
};

export type TransactionType = 'income' | 'expense' | 'transfer';
export type TransactionSource = 'manual' | 'ai_parsed' | 'recurring';
export type CategoryType = 'income' | 'expense';

export type Category = {
  id: string;
  name: string;
  name_en: string;
  name_fa: string | null;
  type: CategoryType;
  icon: string;
  color: string | null;
  parent_id: string | null;
};

export type Transaction = {
  id: string;
  account_id: string;
  to_account_id: string | null;
  category_id: string | null;
  type: TransactionType;
  amount: string;
  currency: string;
  merchant: string | null;
  description: string | null;
  occurred_at: string;
  source: TransactionSource;
  created_at: string;
  updated_at: string;
};

export type TransactionCreatePayload = {
  type: TransactionType;
  account_id: string;
  amount: string;
  occurred_at: string;
  to_account_id?: string | null;
  category_id?: string | null;
  merchant?: string | null;
  description?: string | null;
};

export type TransactionPatchPayload = Partial<TransactionCreatePayload>;

export type TransactionListFilters = {
  account_id?: string;
  category_id?: string;
  type?: TransactionType;
  start?: string;
  end?: string;
  limit?: number;
  offset?: number;
};

export type DashboardSummary = {
  totals_by_currency: CurrencyTotal[];
  account_count: number;
  default_currency: string | null;
  recent_transactions: Transaction[];
};

export type BudgetPeriod = 'weekly' | 'monthly' | 'yearly';

export type Budget = {
  id: string;
  category_id: string;
  amount: string;
  spent: string;
  ratio: number;
  currency: string;
  period: BudgetPeriod;
  is_active: boolean;
  period_start: string;
  period_end: string;
};

export type BudgetCreatePayload = {
  category_id: string;
  amount: string;
  currency: string;
  period: BudgetPeriod;
};
