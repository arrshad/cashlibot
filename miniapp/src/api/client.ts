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
  GamificationStatus,
  Reminder,
  ReminderCreatePayload,
  SavingsGoal,
  SavingsGoalCreatePayload,
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
