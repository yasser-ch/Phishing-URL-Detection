import { NavLink } from "react-router-dom"
import { LayoutDashboard, Search, TriangleAlert, Clock, Settings, ShieldCheck } from "lucide-react"

const NAV_ITEMS = [
  { to: "/", label: "Vue d'ensemble", icon: LayoutDashboard, end: true },
  { to: "/scanner", label: "Scanner", icon: Search },
  { to: "/alerts", label: "Alertes", icon: TriangleAlert },
  { to: "/history", label: "Historique", icon: Clock },
  { to: "/settings", label: "Paramètres", icon: Settings },
]

export default function Sidebar() {
  return (
    <div className="sidebar">
      <div className="sidebar-brand">
        <ShieldCheck size={20} color="var(--primary)" />
        CMRPI
      </div>
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) => `sidebar-nav-item${isActive ? " active" : ""}`}
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}