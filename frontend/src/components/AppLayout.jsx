import { LogOut, Martini, ShieldCheck, UserRound } from 'lucide-react';
import { Link, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';

export default function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="brand" to={user?.role === 'admin' ? '/admin' : '/employee'}>
          <Martini size={22} />
          <span>FestivaPro</span>
        </Link>
        <div className="topbar-actions">
          {user && (
            <span className="identity">
              {user.role === 'admin' ? <ShieldCheck size={16} /> : <UserRound size={16} />}
              {user.full_name}
            </span>
          )}
          <button className="icon-button" onClick={logout} title="Log out" type="button">
            <LogOut size={18} />
          </button>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
