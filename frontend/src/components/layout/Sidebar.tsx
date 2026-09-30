import { useEffect, useRef } from "react";
import { NavLink } from "react-router-dom";
import { Icon, type IconName } from "../ui/Icon";
import tiraLogo from "../../assets/tira-logo.jpeg";

interface NavItem {
  to: string;
  label: string;
  icon: IconName;
  end?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Dashboard", icon: "dashboard", end: true },
  { to: "/reviews", label: "Reviews", icon: "reviews" },
  { to: "/repositories", label: "Repositories", icon: "repositories" },
];

export function Sidebar({
  collapsed,
  onToggleCollapsed,
  mobileOpen,
  onCloseMobile,
}: {
  collapsed: boolean;
  onToggleCollapsed: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}) {
  const navRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!mobileOpen) return;
    const firstLink = navRef.current?.querySelector<HTMLElement>("a");
    firstLink?.focus();
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCloseMobile();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [mobileOpen, onCloseMobile]);

  return (
    <>
      {mobileOpen && <div className="sidebar-overlay" onClick={onCloseMobile} />}
      <aside
        className={`sidebar ${collapsed ? "sidebar--collapsed" : ""} ${mobileOpen ? "sidebar--mobile-open" : ""}`}
        role="dialog"
        aria-modal={mobileOpen || undefined}
        aria-label="Primary navigation"
      >
        <div className="sidebar-header">
          <img className="sidebar-logo" src={tiraLogo} alt="" aria-hidden="true" />
          <div className="sidebar-brand">
            <div className="sidebar-brand-name">TIRA</div>
            <div className="sidebar-brand-full">TI Review Assistant</div>
          </div>
        </div>

        <nav className="sidebar-nav" ref={navRef}>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `sidebar-link${isActive ? " active" : ""}`}
              title={collapsed ? item.label : undefined}
              onClick={onCloseMobile}
            >
              <span className="sidebar-link-icon">
                <Icon name={item.icon} />
              </span>
              <span className="sidebar-link-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button
            type="button"
            className="sidebar-toggle"
            onClick={onToggleCollapsed}
            aria-expanded={!collapsed}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <Icon name={collapsed ? "chevron-right" : "chevron-left"} size={16} />
            {!collapsed && <span>Collapse</span>}
          </button>
        </div>
      </aside>
    </>
  );
}
