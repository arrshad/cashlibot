export type Overview = {
  total_users: number;
  admins: number;
  dau: number;
  wau: number;
  mau: number;
  credits_in_circulation: number;
  ai_credits_spent_this_month: number;
  stars_revenue_this_month: number;
  stars_purchases_this_month: number;
  credits_granted_via_stars_this_month: number;
};

export type UserRow = {
  telegram_id: number;
  username: string | null;
  display_name: string;
  language_code: string;
  default_currency: string | null;
  credit_balance: number;
  is_admin: boolean;
  onboarding_completed: boolean;
  created_at: string;
  last_tx_at: string | null;
  tx_count: number;
};

export type UserList = {
  total: number;
  limit: number;
  offset: number;
  rows: UserRow[];
};

export type CreditHistoryRow = {
  id: string;
  change_amount: number;
  balance_after: number;
  reason: string;
  reference_id: string | null;
  created_at: string;
};

export type UserDetail = UserRow & {
  credit_history: CreditHistoryRow[];
};

export type CreditAdjustPayload = {
  change: number;
  reference?: string | null;
};
