import { BarChart3, BadgeDollarSign, CalendarDays, FolderTree, LogOut, Package, Settings, ShieldCheck, UsersRound, UserRound } from 'lucide-react';
import { Link, NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';

export default function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand sidebar-brand" to={user?.role === 'admin' ? '/admin' : '/employee'}>
          <img alt="FestivaPro logo" src="/festivaprologo.png" />
          <span>FestivaPro</span>
        </Link>
        {user?.role === 'admin' && (
          <nav className="side-nav">
            <NavLink to="/admin/events"><CalendarDays size={17} />Événements</NavLink>
            <NavLink to="/admin/users"><UsersRound size={17} />Utilisateurs</NavLink>
            <NavLink to="/admin/categories"><FolderTree size={17} />Catégories</NavLink>
            <NavLink to="/admin/products"><Package size={17} />Produits</NavLink>
            <NavLink to="/admin/event-stock"><BadgeDollarSign size={17} />Stock événement</NavLink>
            <NavLink to="/admin/reports"><BarChart3 size={17} />Rapports</NavLink>
            <NavLink to="/admin/audit"><Settings size={17} />Audit</NavLink>
          </nav>
        )}
      </aside>
      <header className="topbar">
        <Link className="brand" to={user?.role === 'admin' ? '/admin' : '/employee'}>
          <img alt="FestivaPro logo" src="/festivaprologo.png" />
          <span>FestivaPro</span>
        </Link>
        <div className="topbar-actions">
          {user && (
            <span className="identity">
              {user.role === 'admin' ? <ShieldCheck size={16} /> : <UserRound size={16} />}
              {user.full_name}
            </span>
          )}
          <button className="icon-button" onClick={logout} title="Déconnexion" type="button">
            <LogOut size={18} />
          </button>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
