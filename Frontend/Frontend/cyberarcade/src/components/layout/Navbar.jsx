import I from "../icons/Icons";
import UserDropdown from "./UserDropdown";

export default function Navbar({ theme, setTheme, user, nav, onLogout, currentPage, clear, currentStreak }) {
  const handleLogout = () => {
    if (onLogout) onLogout();
    nav("landing");
  };

  return (
    <nav className={`nv ${clear ? "nc" : ""}`}>
      <div className="ni">

        {/* Logo */}
        <div
          className="br"
          onClick={() => nav("landing")}
          style={{ cursor: "pointer" }}
        >
          {/* Updated logo: hexagonal cyber emblem */}
          <div className="bm">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
              <polygon
                points="14,1 25,7 25,21 14,27 3,21 3,7"
                fill="var(--accent)"
                stroke="var(--accent-bright)"
                strokeWidth="1.5"
              />
              <polygon
                points="14,5 22,9.5 22,18.5 14,23 6,18.5 6,9.5"
                fill="none"
                stroke="var(--cream)"
                strokeWidth="0.8"
                opacity="0.4"
              />
              {/* Lock body */}
              <rect x="10" y="14" width="8" height="6" rx="1" fill="var(--cream)" opacity="0.92"/>
              {/* Lock shackle */}
              <path d="M11.5 14v-2.5a2.5 2.5 0 0 1 5 0V14" stroke="var(--cream)" strokeWidth="1.4" fill="none" opacity="0.92" strokeLinecap="round"/>
              {/* Keyhole */}
              <circle cx="14" cy="16.8" r="1" fill="var(--accent)"/>
              <rect x="13.4" y="17.5" width="1.2" height="1.5" rx="0.4" fill="var(--accent)"/>
            </svg>
          </div>
          <span className="bn">CYBER<span className="ba">ARCADE</span></span>
        </div>

        <div className="nr">
          {/* Home — always visible */}
          <button
            className={`nl ${currentPage === "landing" ? "nl-act" : ""}`}
            onClick={() => nav("landing")}
          >
            Home
          </button>

          {/* Courses — always visible */}
          <button
            className={`nl ${["courses", "course-detail"].includes(currentPage) ? "nl-act" : ""}`}
            onClick={() => nav("courses")}
          >
            Courses
          </button>

          {/* Dashboard — logged-in only */}
          {user && (
            <button
              className={`nl ${currentPage === "dashboard" ? "nl-act" : ""}`}
              onClick={() => nav("dashboard")}
            >
              Dashboard
            </button>
          )}

          {user && (
            <button
              className={`nl ${currentPage === "ai-coach" ? "nl-act" : ""}`}
              onClick={() => nav("ai-coach")}
            >
              AI Coach
            </button>
          )}

          {user && (
            <button
              className={`nl ${currentPage === "badges" ? "nl-act" : ""}`}
              onClick={() => nav("badges")}
            >
              Badges
            </button>
          )}


          {/* Streak chip */}
          {user && (
            <div className="nv-streak" title={`${currentStreak}-day streak`}>
              <span className={`nv-streak-icon${currentStreak > 0 ? " nv-streak-on" : " nv-streak-off"}`}>
                <I.Flame />
              </span>
              <span className="nv-streak-num">{currentStreak}</span>
            </div>
          )}

          {/* Theme toggle */}
          <button className="tt" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} title="Toggle theme">
            {theme === "dark" ? <I.Sun /> : <I.Moon />}
          </button>

          {/* Auth section */}
          {user ? (
            <UserDropdown user={user} nav={nav} onLogout={handleLogout} />
          ) : (
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn bg bs" onClick={() => nav("login")}>Sign In</button>
              <button className="btn ba2 bs" onClick={() => nav("register")}>Register</button>
            </div>
          )}
        </div>
      </div>

      <style>{`
        .nl-act { color: var(--text-primary) !important; background: var(--bg-input) !important; }
      `}</style>
    </nav>
  );
}
