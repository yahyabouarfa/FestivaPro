import { NavLink, Outlet } from "react-router-dom";
import {
  Bell,
  Boxes,
  BriefcaseBusiness,
  CalendarDays,
  ClipboardList,
  DollarSign,
  LineChart,
  LayoutDashboard,
  LogOut,
  Martini,
  Menu,
  Route,
  ShieldCheck,
  UserRoundCog,
  UsersRound,
  Warehouse,
  X
} from "lucide-react";
import { useState } from "react";
import { Button } from "../components/Button";
import { useAuth } from "../context/AuthContext";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/events", label: "Events", icon: CalendarDays },
  { to: "/bars", label: "Bars", icon: Martini },
  { to: "/employees", label: "Employees", icon: UsersRound },
  { to: "/stock", label: "Stock", icon: Warehouse },
  { to: "/equipment", label: "Equipment", icon: Boxes },
  { to: "/logistics", label: "Logistics", icon: Route },
  { to: "/salaries", label: "Salaries", icon: DollarSign },
  { to: "/contributions", label: "Contributions", icon: UserRoundCog },
  { to: "/profits", label: "Profits", icon: BriefcaseBusiness },
  { to: "/night-management", label: "Night", icon: ShieldCheck },
  { to: "/reports", label: "Reports", icon: ClipboardList },
  { to: "/analytics", label: "Analytics", icon: LineChart },
  { to: "/audit-logs", label: "Audit Logs", icon: ClipboardList },
  { to: "/notifications", label: "Notifications", icon: Bell }
];

export function AppShell() {
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuth();

  const sidebar = (
    <aside className="flex h-full w-72 flex-col border-r border-white/10 bg-night/85 p-4 backdrop-blur-xl">
      <div className="mb-6 flex items-center gap-3">
        <img src="/FestivaPro.png" alt="FestivaPro" className="h-12 w-12 rounded-lg object-contain shadow-glow" />
        <div>
          <p className="text-sm font-semibold uppercase text-slate-400">FestivaPro</p>
          <h1 className="text-lg font-bold text-white">Event Management</h1>
        </div>
      </div>
      <nav className="grid gap-1 overflow-y-auto pr-1">
        {nav.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={() => setOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                isActive ? "bg-white/[0.12] text-white shadow-glow" : "text-slate-400 hover:bg-white/[0.08] hover:text-white"
              }`
            }
          >
            <Icon className="h-4 w-4" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto border-t border-white/10 pt-4">
        <p className="text-sm font-medium text-white">{user?.full_name}</p>
        <p className="text-xs text-slate-400">{user?.role}</p>
        <Button variant="ghost" className="mt-3 w-full justify-start" onClick={logout}>
          <LogOut className="h-4 w-4" />
          Sign out
        </Button>
      </div>
    </aside>
  );

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[18rem_1fr]">
      <div className="hidden lg:block">{sidebar}</div>
      {open ? <div className="fixed inset-0 z-40 bg-black/70 lg:hidden" onClick={() => setOpen(false)} /> : null}
      <div className={`fixed inset-y-0 left-0 z-50 transition lg:hidden ${open ? "translate-x-0" : "-translate-x-full"}`}>
        {sidebar}
      </div>
      <main className="min-w-0">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-white/10 bg-night/70 px-4 backdrop-blur-xl sm:px-6">
          <button
            className="focus-ring rounded-lg border border-white/10 bg-white/5 p-2 text-white lg:hidden"
            onClick={() => setOpen((value) => !value)}
            aria-label="Toggle navigation"
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          <div className="hidden sm:block">
            <p className="text-sm text-slate-400">Moroccan premium nightlife operations</p>
          </div>
          <div className="h-2 w-32 rounded-full bg-[image:var(--gradient-neon)] shadow-glow" />
        </header>
        <div className="mx-auto w-full max-w-7xl p-4 sm:p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
