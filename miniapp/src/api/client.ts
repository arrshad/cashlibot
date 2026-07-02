import axios from 'axios';
import { getInitDataRaw } from '@/telegram';
import type {
  Account,
  AccountCreatePayload,
  AccountPatchPayload,
  AppConfig,
  Budget,
  BudgetCreatePayload,
  ContributePayload,
  ContributeResult,
  CreditsStatus,
  GamificationStatus,
  InvoiceLink,
  FriendBalance,
  Friendship,
  FriendsOverview,
  RecurringCreatePayload,
  RecurringTemplate,
  Reminder,
  ReminderCreatePayload,
  ReportPeriod,
  ReportSummary,
  SharedExpense,
  SharedExpenseCreatePayload,
  SharedExpenseSplit,
  SharedExpensesOverview,
  SavingsGoal,
  SavingsGoalCreatePayload,
  UserPatchPayload,
  Category,
  CategoryType,
  DashboardSummary,
  Me,
  OnboardingPayload,
  OnboardingResult,
  Transaction,
  TransactionCreatePayload,
  TransactionListFilters,
  TransactionPatchPayload,
} from '@/types';

// In dev, the Mini App is served on :5173 and the API runs at :8000.
// In prod the Mini App is reverse-proxied to the same origin as the API,
// so the empty-string base just resolves relatively.
const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

const http = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
});

http.interceptors.request.use((config) => {
  const initData = getInitDataRaw();
  if (initData) {
    config.headers.Authorization = `tma ${initData}`;
  }
  return config;
});

export async function fetchMe(): Promise<Me> {
  const { data } = await http.get<Me>('/api/me');
  return data;
}

export async function patchMe(payload: UserPatchPayload): Promise<Me> {
  const { data } = await http.patch<Me>('/api/me', payload);
  return data;
}

export async function fetchCredits(): Promise<CreditsStatus> {
  const { data } = await http.get<CreditsStatus>('/api/credits');
  return data;
}

export async function createPurchaseInvoice(packageId: string): Promise<InvoiceLink> {
  const { data } = await http.post<InvoiceLink>(
    `/api/credits/purchase/${packageId}`,
  );
  return data;
}

export async function fetchConfig(): Promise<AppConfig> {
  const { data } = await http.get<AppConfig>('/api/config');
  return data;
}

export async function completeOnboarding(
  payload: OnboardingPayload,
): Promise<OnboardingResult> {
  const { data } = await http.post<OnboardingResult>(
    '/api/onboarding/complete',
    payload,
  );
  return data;
}

export async function fetchAccounts(): Promise<Account[]> {
  const { data } = await http.get<Account[]>('/api/accounts');
  return data;
}

export async function createAccount(payload: AccountCreatePayload): Promise<Account> {
  const { data } = await http.post<Account>('/api/accounts', payload);
  return data;
}

export async function updateAccount(
  id: string,
  payload: AccountPatchPayload,
): Promise<Account> {
  const { data } = await http.patch<Account>(`/api/accounts/${id}`, payload);
  return data;
}

export async function archiveAccount(id: string): Promise<void> {
  await http.delete(`/api/accounts/${id}`);
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await http.get<DashboardSummary>('/api/dashboard/summary');
  return data;
}

export async function fetchCategories(type?: CategoryType): Promise<Category[]> {
  const { data } = await http.get<Category[]>('/api/categories', {
    params: type ? { type } : undefined,
  });
  return data;
}

export async function fetchTransactions(
  filters: TransactionListFilters = {},
): Promise<Transaction[]> {
  const { data } = await http.get<Transaction[]>('/api/transactions', {
    params: filters,
  });
  return data;
}

export async function createTransaction(
  payload: TransactionCreatePayload,
): Promise<Transaction> {
  const { data } = await http.post<Transaction>('/api/transactions', payload);
  return data;
}

export async function updateTransaction(
  id: string,
  payload: TransactionPatchPayload,
): Promise<Transaction> {
  const { data } = await http.patch<Transaction>(`/api/transactions/${id}`, payload);
  return data;
}

export async function deleteTransaction(id: string): Promise<void> {
  await http.delete(`/api/transactions/${id}`);
}

export async function fetchBudgets(): Promise<Budget[]> {
  const { data } = await http.get<Budget[]>('/api/budgets');
  return data;
}

export async function createBudget(payload: BudgetCreatePayload): Promise<Budget> {
  const { data } = await http.post<Budget>('/api/budgets', payload);
  return data;
}

export async function deleteBudget(id: string): Promise<void> {
  await http.delete(`/api/budgets/${id}`);
}

export async function fetchGoals(): Promise<SavingsGoal[]> {
  const { data } = await http.get<SavingsGoal[]>('/api/goals');
  return data;
}

export async function createGoal(
  payload: SavingsGoalCreatePayload,
): Promise<SavingsGoal> {
  const { data } = await http.post<SavingsGoal>('/api/goals', payload);
  return data;
}

export async function contributeToGoal(
  id: string,
  payload: ContributePayload,
): Promise<ContributeResult> {
  const { data } = await http.post<ContributeResult>(
    `/api/goals/${id}/contribute`,
    payload,
  );
  return data;
}

export async function deleteGoal(id: string): Promise<void> {
  await http.delete(`/api/goals/${id}`);
}

export async function fetchGamification(): Promise<GamificationStatus> {
  const { data } = await http.get<GamificationStatus>('/api/gamification/status');
  return data;
}

export async function fetchReminders(): Promise<Reminder[]> {
  const { data } = await http.get<Reminder[]>('/api/reminders');
  return data;
}

export async function createReminder(
  payload: ReminderCreatePayload,
): Promise<Reminder> {
  const { data } = await http.post<Reminder>('/api/reminders', payload);
  return data;
}

export async function deleteReminder(id: string): Promise<void> {
  await http.delete(`/api/reminders/${id}`);
}

export async function fetchRecurring(): Promise<RecurringTemplate[]> {
  const { data } = await http.get<RecurringTemplate[]>('/api/recurring');
  return data;
}

export async function createRecurring(
  payload: RecurringCreatePayload,
): Promise<RecurringTemplate> {
  const { data } = await http.post<RecurringTemplate>('/api/recurring', payload);
  return data;
}

export async function deleteRecurring(id: string): Promise<void> {
  await http.delete(`/api/recurring/${id}`);
}

export async function fetchFriends(): Promise<FriendsOverview> {
  const { data } = await http.get<FriendsOverview>('/api/friends');
  return data;
}

export async function sendFriendRequest(username: string): Promise<Friendship> {
  const { data } = await http.post<Friendship>('/api/friends', { username });
  return data;
}

export async function acceptFriend(id: string): Promise<Friendship> {
  const { data } = await http.post<Friendship>(`/api/friends/${id}/accept`);
  return data;
}

export async function declineFriend(id: string): Promise<Friendship> {
  const { data } = await http.post<Friendship>(`/api/friends/${id}/decline`);
  return data;
}

export async function fetchSharedExpenses(): Promise<SharedExpensesOverview> {
  const { data } = await http.get<SharedExpensesOverview>('/api/shared-expenses');
  return data;
}

export async function createSharedExpense(
  payload: SharedExpenseCreatePayload,
): Promise<SharedExpense> {
  const { data } = await http.post<SharedExpense>('/api/shared-expenses', payload);
  return data;
}

export async function approveSplit(splitId: string): Promise<SharedExpenseSplit> {
  const { data } = await http.post<SharedExpenseSplit>(
    `/api/shared-expenses/splits/${splitId}/approve`,
  );
  return data;
}

export async function disputeSplit(splitId: string): Promise<SharedExpenseSplit> {
  const { data } = await http.post<SharedExpenseSplit>(
    `/api/shared-expenses/splits/${splitId}/dispute`,
  );
  return data;
}

export async function fetchFriendBalance(friendId: number): Promise<FriendBalance> {
  const { data } = await http.get<FriendBalance>(
    `/api/shared-expenses/friends/${friendId}/balance`,
  );
  return data;
}

export async function settleWithFriend(
  friendId: number,
): Promise<{ splits_settled: number }> {
  const { data } = await http.post<{ splits_settled: number }>(
    `/api/shared-expenses/friends/${friendId}/settle`,
  );
  return data;
}

export async function fetchReportSummary(
  period: ReportPeriod,
): Promise<ReportSummary> {
  const { data } = await http.get<ReportSummary>('/api/reports/summary', {
    params: { period },
  });
  return data;
}

// The Authorization header carries initData, so we can't just hit the URL —
// we fetch as a blob and trigger a download programmatically. Falls back to
// the browser's default filename if the response omits Content-Disposition.
export async function downloadExport(
  path: '/api/export/data.json' | '/api/export/transactions.csv',
): Promise<void> {
  const response = await http.get(path, { responseType: 'blob' });
  const disposition = String(response.headers['content-disposition'] ?? '');
  const match = disposition.match(/filename="?([^"]+)"?/i);
  const filename = match?.[1] ?? path.split('/').pop() ?? 'cashlibot-export';

  const url = URL.createObjectURL(response.data as Blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
