import {
  BarChart3,
  Bot,
  BriefcaseBusiness,
  ChevronDown,
  Compass,
  Languages,
  LayoutDashboard,
  LogOut,
  Milestone,
  ShieldCheck,
  Target,
  UserRound,
} from "lucide-react";
import { type ReactNode } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";

import { useDemo } from "../context/DemoContext";
import type { DemoRole, Language } from "../types";


interface AppShellProps {
  children: ReactNode;
  employeeId?: string;
  title?: string;
  eyebrow?: string;
}

const navItems = [
  { key: "dashboard", segment: "dashboard", icon: LayoutDashboard },
  { key: "career", segment: "career", icon: Milestone },
  { key: "skills", segment: "skills", icon: Target },
  { key: "quests", segment: "quests", icon: Compass },
  { key: "coach", segment: "coach", icon: Bot },
] as const;

export function AppShell({ children, employeeId: propEmployeeId, title, eyebrow }: AppShellProps) {
  const { employeeId: storedEmployeeId, setEmployeeId, language, setLanguage, role, setRole, t } = useDemo();
  const employeeId = propEmployeeId || storedEmployeeId || undefined;
  const navigate = useNavigate();
  const location = useLocation();

  function changeRole(nextRole: DemoRole) {
    setRole(nextRole);
    if (nextRole === "hr") navigate("/hr");
    else navigate(employeeId ? `/dashboard/${employeeId}` : "/");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label={t("primaryNavigation")}>
        <NavLink className="brand" to={employeeId ? `/dashboard/${employeeId}` : "/"}>
          <span className="brand-mark"><BriefcaseBusiness size={22} aria-hidden="true" /></span>
          <span><strong>Career Quest</strong><small>{t("growthWorkspace")}</small></span>
        </NavLink>
        <nav className="sidebar-nav">
          {employeeId && role === "employee" ? navItems.map(({ key, segment, icon: Icon }) => (
            <NavLink key={key} className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`} to={`/${segment}/${employeeId}`}>
              <Icon size={19} aria-hidden="true" /><span>{t(key)}</span>
            </NavLink>
          )) : null}
          {role === "hr" ? (
            <NavLink className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`} to="/hr">
              <BarChart3 size={19} aria-hidden="true" /><span>{t("hrView")}</span>
            </NavLink>
          ) : null}
        </nav>
        <div className="sidebar-foot">
          {employeeId ? (
            <NavLink className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`} to={`/profile/${employeeId}`}>
              <UserRound size={19} aria-hidden="true" /><span>{t("profile")}</span>
            </NavLink>
          ) : null}
          <button
            className="nav-item button-reset"
            type="button"
            onClick={() => { setEmployeeId(null); setRole("employee"); navigate("/"); }}
          >
            <LogOut size={19} aria-hidden="true" /><span>{t("selectAnother")}</span>
          </button>
        </div>
      </aside>

      <div className="app-content">
        <header className="topbar">
          <div className="topbar-title">
            {eyebrow ? <span>{eyebrow}</span> : null}
            <h1>{title || "Career Quest"}</h1>
          </div>
          <div className="topbar-actions">
            <div className="segmented" aria-label={t("demoRole")}>
              <button type="button" className={role === "employee" ? "active" : ""} onClick={() => changeRole("employee")}>
                <UserRound size={15} /><span>{t("employee")}</span>
              </button>
              <button type="button" className={role === "hr" ? "active" : ""} onClick={() => changeRole("hr")}>
                <ShieldCheck size={15} /><span>{t("hr")}</span>
              </button>
            </div>
            <label className="language-select">
              <Languages size={17} aria-hidden="true" />
              <span className="sr-only">{t("language")}</span>
              <select value={language} onChange={(event) => setLanguage(event.target.value as Language)}>
                <option value="ru">RU</option>
                <option value="en">EN</option>
                <option value="kk">KZ</option>
              </select>
              <ChevronDown size={14} aria-hidden="true" />
            </label>
          </div>
        </header>
        <main id="main-content" className="main-content">{children}</main>
      </div>

      {employeeId && role === "employee" && location.pathname !== "/" ? (
        <nav className="mobile-nav" aria-label={t("mobileNavigation")}>
          {navItems.map(({ key, segment, icon: Icon }) => (
            <NavLink key={key} className={({ isActive }) => isActive ? "active" : ""} to={`/${segment}/${employeeId}`}>
              <Icon size={20} aria-hidden="true" /><span>{t(key)}</span>
            </NavLink>
          ))}
        </nav>
      ) : null}
    </div>
  );
}
