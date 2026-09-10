import NotificationBell from "./NotificationBell";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { BarChart3, ClipboardCheck, FileText, GraduationCap, LayoutDashboard, Menu, Settings, Users, X, LogOut, Building2 } from "lucide-react";
import LogoPlaceholder from "./LogoPlaceholder";
import { useAuth } from "../auth/AuthContext";
import type { Role } from "../types";

const links: { to: string; label: string; icon: typeof Users; roles: Role[] }[] = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, roles: ["HR_ADMIN", "MANAGER", "EMPLOYEE"] },
  { to: "/trainings", label: "Trainings", icon: GraduationCap, roles: ["HR_ADMIN", "MANAGER"] },
  { to: "/attendance", label: "Attendance", icon: ClipboardCheck, roles: ["HR_ADMIN", "MANAGER", "EMPLOYEE"] },
  { to: "/feedback", label: "Feedback", icon: FileText, roles: ["HR_ADMIN", "MANAGER", "EMPLOYEE"] },
  { to: "/employees", label: "Employees", icon: Users, roles: ["HR_ADMIN"] },
  { to: "/departments", label: "Departments", icon: Building2, roles: ["HR_ADMIN"] },
  { to: "/analytics", label: "Analytics", icon: BarChart3, roles: ["HR_ADMIN", "MANAGER"] },
  { to: "/reports", label: "Reports", icon: FileText, roles: ["HR_ADMIN", "MANAGER"] },
  { to: "/evaluations", label: "Effectiveness", icon: BarChart3, roles: ["HR_ADMIN", "MANAGER"] },
  { to: "/settings", label: "Settings", icon: Settings, roles: ["HR_ADMIN", "MANAGER", "EMPLOYEE"] },
];

export default function AppShell() {
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuth();
  const visibleLinks = links.filter(link => user && link.roles.includes(user.role));
  const initials = user?.name.split(" ").map(x => x[0]).slice(0, 2).join("").toUpperCase() ?? "U";

  return <div className="min-h-screen bg-slate-50">
    {open && <button aria-label="Close navigation" className="fixed inset-0 z-30 bg-slate-950/30 lg:hidden" onClick={() => setOpen(false)} />}
    <aside className={`fixed inset-y-0 left-0 z-40 w-72 transform border-r border-slate-200 bg-white transition-transform lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
      <div className="flex h-20 items-center gap-3 border-b border-slate-100 px-5"><LogoPlaceholder /><div><p className="text-sm font-bold">Training Management</p><p className="text-xs text-slate-500">Employee Portal</p></div><button className="ml-auto lg:hidden" onClick={()=>setOpen(false)}><X size={20}/></button></div>
      <nav className="space-y-1 p-4">{visibleLinks.map(({to,label,icon:Icon}) => <NavLink key={to} to={to} end={to==="/"} onClick={()=>setOpen(false)} className={({isActive})=>`flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium ${isActive?"bg-indigo-50 text-indigo-700":"text-slate-600 hover:bg-slate-50 hover:text-slate-900"}`}><Icon size={18}/>{label}</NavLink>)}</nav>
      <div className="absolute bottom-0 w-full border-t border-slate-100 p-4"><button onClick={logout} className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-600 hover:bg-slate-50"><LogOut size={18}/> Logout</button></div>
    </aside>
    <div className="lg:pl-72">
      <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur sm:px-6 lg:px-8"><button className="rounded-xl p-2 hover:bg-slate-100 lg:hidden" onClick={()=>setOpen(true)}><Menu size={22}/></button><div className="hidden lg:block"><p className="text-sm text-slate-500">Employee Training Management</p><p className="text-lg font-semibold">Training & Effectiveness Portal</p></div><div className="ml-auto flex items-center gap-3"><NotificationBell /><div className="hidden text-right sm:block"><p className="text-sm font-semibold">{user?.name}</p><p className="text-xs text-slate-500">{user?.role.replace("_", " / ")}</p></div><div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-100 font-semibold text-indigo-700">{initials}</div></div></header>
      <main className="p-4 sm:p-6 lg:p-8"><Outlet /></main>
    </div>
  </div>;
}
