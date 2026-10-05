import { useState, useRef, useEffect } from "react";
import I from "../icons/Icons";

export default function UserDropdown({ user, nav, onLogout }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  // Close on click outside
  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const initials = (user?.full_name || "U")
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  const roleBadge = {
    student: { label: "Student", cls: "role-student" },
    instructor: { label: "Instructor", cls: "role-instructor" },
    admin: { label: "Admin", cls: "role-admin" },
    system_admin: { label: "System Admin", cls: "role-admin" },
  }[user?.role] || { label: "User", cls: "role-student" };

  const isAdmin = ["admin", "system_admin"].includes(user?.role);
  const isInstructor = ["instructor", "admin", "system_admin"].includes(user?.role);

  const go = (page) => {
    setOpen(false);
    nav(page);
  };

  return (
    <div className="ud-wrap" ref={ref}>
      <button className="ud-trigger" onClick={() => setOpen(!open)} id="user-dropdown-trigger">
        <div className="ud-avatar">{initials}</div>
        <I.ChevronDown />
      </button>

      {open && (
        <div className="ud-menu" id="user-dropdown-menu">
          {/* Header */}
          <div className="ud-header">
            <div className="ud-avatar ud-avatar-lg">{initials}</div>
            <div className="ud-info">
              <span className="ud-name">{user?.full_name}</span>
              <span className="ud-email">{user?.email}</span>
              <span className={`ud-role ${roleBadge.cls}`}>{roleBadge.label}</span>
            </div>
          </div>

          <div className="ud-divider" />

          {/* Navigation items */}
          <button className="ud-item" onClick={() => go("profile")}>
            <I.User /> Profile
          </button>
          <button className="ud-item" onClick={() => go("dashboard")}>
            <I.Monitor /> Dashboard
          </button>
          <button className="ud-item" onClick={() => go("ai-coach")}>
            <I.Bot /> AI Coach
          </button>
          <button className="ud-item" onClick={() => go("badges")}>
            <I.Award /> Badges
          </button>
          <button className="ud-item" onClick={() => go("subscription")}>
            <I.Crown /> Subscription
          </button>

          <button className="ud-item" onClick={() => go("settings")}>
            <I.Settings /> Settings
          </button>

          {isInstructor && (
            <button className="ud-item" onClick={() => go("instructor")}>
              <I.Users /> Instructor Panel
            </button>
          )}

          {isAdmin && (
            <button className="ud-item" onClick={() => go("admin")}>
              <I.Settings /> Admin Panel
            </button>
          )}

          <div className="ud-divider" />

          <button className="ud-item ud-logout" onClick={() => { setOpen(false); onLogout(); }}>
            <I.LogOut /> Sign Out
          </button>
        </div>
      )}
    </div>
  );
}
