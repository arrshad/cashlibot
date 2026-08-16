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
import { AddReminder } from '@/pages/reminders/AddReminder';
import { ReminderList } from '@/pages/reminders/ReminderList';
import { AddRecurring } from '@/pages/recurring/AddRecurring';
import { RecurringList } from '@/pages/recurring/RecurringList';
import { FriendList } from '@/pages/friends/FriendList';
import { FriendDetail } from '@/pages/friends/FriendDetail';
import { AddSharedExpense } from '@/pages/friends/AddSharedExpense';
import { ReportsPage } from '@/pages/reports/ReportsPage';
import { CreditsPage } from '@/pages/credits/CreditsPage';
import { SettingsPage } from '@/pages/settings/SettingsPage';
import { QuickAdd } from '@/pages/transactions/QuickAdd';
import { TransactionList } from '@/pages/transactions/TransactionList';
import { TabBar } from '@/components/TabBar';
import { t } from '@/i18n';
import { useAppStore } from '@/store/app';
import { useNavStore } from '@/store/nav';
import { getInitDataRaw, notifyReady } from '@/telegram';
import type { Route } from '@/store/nav';

type TopTab = 'home' | 'budget' | 'goals' | 'reports' | 'settings';

// Routes that render with the bottom tab bar visible.
const TAB_FOR_ROUTE: Partial<Record<Route['name'], TopTab>> = {
  dashboard: 'home',
  budgets: 'budget',
  goals: 'goals',
  reports: 'reports',
  settings: 'settings',
};

const ROUTE_FOR_TAB: Record<TopTab, Route> = {
  home: { name: 'dashboard' },
  budget: { name: 'budgets' },
  goals: { name: 'goals' },
  reports: { name: 'reports' },
  settings: { name: 'settings' },
};

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
  const activeTab = TAB_FOR_ROUTE[route.name];

  const page = renderPage(route, go, lang);

  return (
    <>
      {page}
      {activeTab && (
        <TabBar<TopTab>
          items={[
            { key: 'home', label: t(lang, 'nav.home'), icon: 'fa-house' },
            { key: 'budget', label: t(lang, 'nav.budget'), icon: 'fa-piggy-bank' },
            { key: 'goals', label: t(lang, 'nav.goals'), icon: 'fa-flag-checkered' },
            { key: 'reports', label: t(lang, 'nav.reports'), icon: 'fa-chart-line' },
            { key: 'settings', label: t(lang, 'nav.settings'), icon: 'fa-gear' },
          ]}
          active={activeTab}
          onSelect={(k) => go(ROUTE_FOR_TAB[k])}
          onFab={() => go({ name: 'add-tx' })}
          fabLabel={t(lang, 'nav.add')}
        />
      )}
    </>
  );
}

function renderPage(route: Route, go: (r: Route) => void, lang: 'en' | 'fa') {
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
    case 'reminders':
      return <ReminderList />;
    case 'add-reminder':
      return <AddReminder />;
    case 'recurring':
      return <RecurringList />;
    case 'add-recurring':
      return <AddRecurring />;
    case 'friends':
      return <FriendList />;
    case 'friend-detail':
      return <FriendDetail friendId={route.friendId} />;
    case 'add-shared-expense':
      return <AddSharedExpense friendId={route.friendId} />;
    case 'reports':
      return <ReportsPage />;
    case 'settings':
      return <SettingsPage />;
    case 'credits':
      return <CreditsPage />;
  }
}
