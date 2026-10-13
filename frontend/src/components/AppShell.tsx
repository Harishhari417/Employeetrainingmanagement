
import NotificationBell from "./NotificationBell";
import CompanyFooter from "./CompanyFooter";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  BarChart3,
  ClipboardCheck,
  FileText,
  GraduationCap,
  LayoutDashboard,
  Menu,
  Settings,
  Users,
  X,
  LogOut,
  Building2,
  ClipboardList,
  ChevronDown,
  UserRound,
  Mail,
  Building2 as BuildingIcon,
  BadgeCheck
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import type { Role } from "../types";

const links: {
  to: string;
  label: string;
  icon: typeof Users;
  roles: Role[];
}[] = [
  {
    to: "/",
    label: "Dashboard",
    icon: LayoutDashboard,
    roles: ["HR_ADMIN", "MANAGER", "EMPLOYEE"]
  },
  {
    to: "/trainings",
    label: "Trainings",
    icon: GraduationCap,
    roles: ["HR_ADMIN", "MANAGER", "EMPLOYEE"]
  },
  {
    to: "/attendance",
    label: "Attendance",
    icon: ClipboardCheck,
    roles: ["HR_ADMIN", "MANAGER", "EMPLOYEE"]
  },
  {
    to: "/feedback",
    label: "Feedback",
    icon: FileText,
    roles: ["HR_ADMIN", "MANAGER", "EMPLOYEE"]
  },
  {
    to: "/evaluations",
    label: "Effectiveness",
    icon: ClipboardList,
    roles: ["HR_ADMIN", "MANAGER", "EMPLOYEE"]
  },
  {
    to: "/employees",
    label: "Employees",
    icon: Users,
    roles: ["HR_ADMIN"]
  },
  {
    to: "/departments",
    label: "Departments",
    icon: Building2,
    roles: ["HR_ADMIN"]
  },
  {
    to: "/analytics",
    label: "Analytics",
    icon: BarChart3,
    roles: ["HR_ADMIN", "MANAGER"]
  },
  {
    to: "/reports",
    label: "Reports",
    icon: FileText,
    roles: ["HR_ADMIN", "MANAGER"]
  },
  {
    to: "/settings",
    label: "Settings",
    icon: Settings,
    roles: ["HR_ADMIN", "MANAGER", "EMPLOYEE"]
  }
];

export default function AppShell() {
  const [open, setOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const { user, logout } = useAuth();

  const visibleLinks = links.filter(
    (link) => user && link.roles.includes(user.role)
  );

  const initials =
    user?.name
      ?.split(" ")
      .map((x) => x[0])
      .slice(0, 2)
      .join("")
      .toUpperCase() ?? "U";

  return (
    <div className="min-h-screen bg-slate-50">
      {open && (
        <button
          aria-label="Close navigation"
          className="fixed inset-0 z-30 bg-slate-950/30 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 w-72 transform border-r border-slate-200 bg-white transition-transform lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-20 items-center gap-3 border-b border-slate-100 px-5">
          <img
            src="/EVIG-Intergration_horizantal_Logo_1500-1.png"
            alt="EVIG Integration"
            className="h-11 w-auto max-w-[150px] object-contain"
          />

          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-bold text-slate-900">
              Training Management
            </p>
            <p className="text-xs text-slate-500">
              Employee Portal
            </p>
          </div>

          <button
            aria-label="Close navigation"
            className="ml-auto rounded-lg p-2 hover:bg-slate-100 lg:hidden"
            onClick={() => setOpen(false)}
          >
            <X size={20} />
          </button>
        </div>

        <nav className="space-y-1 overflow-y-auto p-4 pb-24">
          {visibleLinks.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition ${
                  isActive
                    ? "bg-indigo-50 text-indigo-700"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                }`
              }
            >
              <Icon size={18} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-0 w-full border-t border-slate-100 bg-white p-4">
          <button
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900"
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>

      <div className="flex min-h-screen flex-col lg:pl-72">
        <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <button
              aria-label="Open navigation"
              className="rounded-xl p-2 hover:bg-slate-100 lg:hidden"
              onClick={() => setOpen(true)}
            >
              <Menu size={22} />
            </button>

            <div className="hidden sm:block lg:hidden">
              <img
                src="/EVIG-Intergration_horizantal_Logo_1500-1.png"
                alt="EVIG Integration"
                className="h-9 w-auto max-w-[140px] object-contain"
              />
            </div>

            <div className="hidden lg:block">
              <p className="text-sm text-slate-500">
                Employee Training Management
              </p>
              <p className="text-lg font-semibold text-slate-900">
                Training & Effectiveness Portal
              </p>
            </div>
          </div>

          <div className="ml-auto flex items-center gap-3">
            <NotificationBell />

            <div className="relative">
              <button type="button" aria-label="View profile details" aria-expanded={profileOpen} onClick={() => setProfileOpen((value) => !value)} className="flex items-center gap-2 rounded-xl p-1.5 text-left hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-indigo-100 font-semibold text-indigo-700">{initials}</span>
                <span className="hidden max-w-40 sm:block"><span className="block truncate text-sm font-semibold text-slate-900">{user?.name || "User"}</span><span className="block text-xs text-slate-500">{user?.role?.replace("_", " / ")}</span></span>
                <ChevronDown size={15} className="hidden text-slate-500 sm:block" />
              </button>
              {profileOpen && <>
                <button aria-label="Close profile details" className="fixed inset-0 z-30 cursor-default" onClick={() => setProfileOpen(false)} />
                <div className="absolute right-0 z-40 mt-2 w-72 rounded-2xl border border-slate-200 bg-white p-4 shadow-xl">
                  <div className="flex items-center gap-3 border-b border-slate-100 pb-3"><span className="flex h-11 w-11 items-center justify-center rounded-full bg-indigo-100 font-semibold text-indigo-700">{initials}</span><div className="min-w-0"><p className="truncate text-sm font-semibold text-slate-900">{user?.name || "User"}</p><p className="text-xs text-slate-500">{user?.role?.replace("_", " / ")}</p></div></div>
                  <div className="space-y-3 pt-3 text-sm text-slate-600">
                    <p className="flex items-start gap-2"><UserRound size={16} className="mt-0.5 shrink-0 text-slate-400"/><span><span className="block text-xs text-slate-400">Employee / login ID</span>{user?.employeeId || user?.username || "Not available"}</span></p>
                    {user?.email && <p className="flex items-start gap-2"><Mail size={16} className="mt-0.5 shrink-0 text-slate-400"/><span className="min-w-0"><span className="block text-xs text-slate-400">Email</span><span className="break-all">{user.email}</span></span></p>}
                    <p className="flex items-start gap-2"><BuildingIcon size={16} className="mt-0.5 shrink-0 text-slate-400"/><span><span className="block text-xs text-slate-400">Department</span>{user?.department || "Not available"}</span></p>
                    {user?.designation && <p className="flex items-start gap-2"><BadgeCheck size={16} className="mt-0.5 shrink-0 text-slate-400"/><span><span className="block text-xs text-slate-400">Designation</span>{user.designation}</span></p>}
                    <p className="flex items-start gap-2"><BadgeCheck size={16} className="mt-0.5 shrink-0 text-slate-400"/><span><span className="block text-xs text-slate-400">Account role</span>{user?.role || "Not available"}</span></p>
                  </div>
                  <button onClick={() => { setProfileOpen(false); logout(); }} className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"><LogOut size={16}/> Sign out</button>
                </div>
              </>}
            </div>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
        <CompanyFooter />
      </div>
    </div>
  );
}

