import { useEffect } from 'react';
import './theme.css';
import { Login } from './pages/Login';
import { Overview } from './pages/Overview';
import { UsersList } from './pages/UsersList';
import { UserDetailPage } from './pages/UserDetail';
import { useAppStore } from './store';

export default function App() {
  const token = useAppStore((s) => s.token);
  const route = useAppStore((s) => s.route);
  const go = useAppStore((s) => s.go);
  const logout = useAppStore((s) => s.logout);

  useEffect(() => {
    if (!token) return;
    // reset scroll on nav
    window.scrollTo({ top: 0 });
  }, [route, token]);

  if (!token) return <Login />;

  const isOverview = route.name === 'overview';
  const isUsers = route.name === 'users' || route.name === 'user';

  return (
    <div className="shell">
      <div className="topbar">
        <h1>Cashlibot Admin</h1>
        <nav>
          <button
            className={isOverview ? 'active' : ''}
            onClick={() => go({ name: 'overview' })}
          >
            Overview
          </button>
          <button
            className={isUsers ? 'active' : ''}
            onClick={() => go({ name: 'users' })}
          >
            Users
          </button>
        </nav>
        <div className="spacer" />
        <button className="btn-ghost" onClick={logout}>
          Sign out
        </button>
      </div>

      {route.name === 'overview' && <Overview />}
      {route.name === 'users' && <UsersList />}
      {route.name === 'user' && <UserDetailPage userId={route.userId} />}
    </div>
  );
}
