import { BarChart3, CalendarDays, Boxes, LogOut, Martini, Settings, ShieldCheck, Store, UsersRound, UserRound } from 'lucide-react';
import { Link, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';

export default function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand sidebar-brand" to={user?.role === 'admin' ? '/admin' : '/employee'}>
          <Martini size={22} />
          <span>FestivaPro</span>
        </Link>
        {user?.role === 'admin' && (
          <nav className="side-nav">
            <a href="#events"><CalendarDays size={17} />Events</a>
            <a href="#bars"><Store size={17} />Bars</a>
            <a href="#stock"><Boxes size={17} />Stock</a>
            <a href="#staff"><UsersRound size={17} />Staff</a>
            <a href="#reports"><BarChart3 size={17} />Reports</a>
            <a href="#settings"><Settings size={17} />Settings</a>
          </nav>
        )}
      </aside>
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
