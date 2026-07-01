import { useEffect } from 'react';
import { Dashboard } from '@/pages/Dashboard';
import { ErrorView } from '@/pages/ErrorView';
import { Loading } from '@/pages/Loading';
import { Onboarding } from '@/pages/onboarding';
import { Outside } from '@/pages/Outside';
import { AddAccount } from '@/pages/dashboard/AddAccount';
import { AddBudget } from '@/pages/budgets/AddBudget';
import { BudgetList } from '@/pages/budgets/BudgetList';
import { AddGoal } from '@/pages/goals/AddGoal';
import { ContributeGoal } from '@/pages/goals/ContributeGoal';
import { GoalList } from '@/pages/goals/GoalList';
import { StatsPage } from '@/pages/gamification/StatsPage';
import { AddReminder } from '@/pages/reminders/AddReminder';
import { ReminderList } from '@/pages/reminders/ReminderList';
import { QuickAdd } from '@/pages/transactions/QuickAdd';
import { TransactionList } from '@/pages/transactions/TransactionList';
import { useAppStore } from '@/store/app';
import { useNavStore } from '@/store/nav';
import { getInitDataRaw, notifyReady } from '@/telegram';

export default function App() {
  const { me, config, loading, error, load } = useAppStore();
  const route = useNavStore((s) => s.route);
  const go = useNavStore((s) => s.go);
  const initData = getInitDataRaw();

  useEffect(() => {
    notifyReady();
    if (initData) load();
  }, [initData, load]);

  if (!initData) return <Outside />;
  if (loading) return <Loading />;
  if (error) return <ErrorView message={error} onRetry={load} />;
  if (!me || !config) return <Loading />;
  if (!me.onboarding_completed) return <Onboarding />;

  const lang = me.language_code;

  switch (route.name) {
    case 'dashboard':
      return <Dashboard />;
    case 'transactions':
      return <TransactionList />;
    case 'add-tx':
      return <QuickAdd />;
    case 'add-account':
      return <AddAccount lang={lang} onDone={() => go({ name: 'dashboard' })} />;
    case 'budgets':
      return <BudgetList />;
    case 'add-budget':
      return <AddBudget />;
    case 'goals':
      return <GoalList />;
    case 'add-goal':
      return <AddGoal />;
    case 'contribute-goal':
      return <ContributeGoal goalId={route.goalId} />;
    case 'stats':
      return <StatsPage />;
    case 'reminders':
      return <ReminderList />;
    case 'add-reminder':
      return <AddReminder />;
  }
}
