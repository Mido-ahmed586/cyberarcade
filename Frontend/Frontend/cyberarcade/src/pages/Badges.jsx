import { useEffect, useState } from "react";
import Navbar from "../components/layout/Navbar";
import { gamificationService } from "../services/gamification.service";
import { InlineLoader } from "../components/ui/Loader";
import { BadgeEmblem, RARITY_COLOR } from "../components/gamification/BadgeCard";

const RARITY_ORDER = { legendary: 0, epic: 1, rare: 2, common: 3 };

const CATEGORY_LABEL = {
  milestone: "Milestones",
  performance: "Performance",
  xp: "XP Achievements",
  streak: "Streaks",
  category: "Specializations",
};

function BadgeDetail({ badge }) {
  const color = RARITY_COLOR[badge.rarity] || RARITY_COLOR.common;
  return (
    <div
      className={`bdg-card${badge.earned ? " bdg-earned" : " bdg-locked"}`}
      style={{ "--bdg-color": color }}
      title={badge.description}
    >
      <BadgeEmblem badge={badge} size={88} />
      <div className="bdg-body">
        <div className="bdg-name">{badge.name}</div>
        <div className="bdg-desc">{badge.description}</div>
        <div className="bdg-footer">
          <span className="bdg-rarity" style={{ color }}>{badge.rarity}</span>
          {badge.xp_reward > 0 && (
            <span className="bdg-xp">+{badge.xp_reward} XP</span>
          )}
          {badge.earned && badge.awarded_at && (
            <span className="bdg-date">
              {new Date(badge.awarded_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}
            </span>
          )}
        </div>
      </div>
      {badge.earned && <div className="bdg-check">✓</div>}
    </div>
  );
}

export default function Badges({ theme, setTheme, user, nav, onLogout, currentPage, userPlan, currentStreak }) {
  const [badges, setBadges] = useState([]);
  const [status, setStatus] = useState("loading");
  const [filter, setFilter] = useState("all"); // all | earned | locked | rarity

  useEffect(() => {
    let cancelled = false;
    gamificationService.badges()
      .then((d) => { if (!cancelled) { setBadges(d || []); setStatus("ready"); } })
      .catch(() => { if (!cancelled) setStatus("error"); });
    return () => { cancelled = true; };
  }, []);

  const earned = badges.filter((b) => b.earned);
  const locked = badges.filter((b) => !b.earned);

  const filtered = filter === "earned" ? earned
    : filter === "locked" ? locked
    : badges;

  // Group by category
  const groups = {};
  filtered.forEach((b) => {
    const cat = b.category || "other";
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(b);
  });
  const RARITY_ASC = { common: 0, rare: 1, epic: 2, legendary: 3 };

  const criteriaNum = (badge) => {
    const c = badge.criteria || {};
    return c.threshold ?? c.amount ?? c.days ?? null;
  };

  // Sort all groups: by criteria number ascending (easy → hard), then rarity ascending
  Object.values(groups).forEach((arr) =>
    arr.sort((a, b) => {
      const an = criteriaNum(a), bn = criteriaNum(b);
      if (an != null && bn != null) return an - bn;
      if (an != null) return -1;
      if (bn != null) return 1;
      return (RARITY_ASC[a.rarity] ?? 4) - (RARITY_ASC[b.rarity] ?? 4);
    })
  );

  return (
    <div className="pg">
      <Navbar theme={theme} setTheme={setTheme} user={user} nav={nav} onLogout={onLogout} currentPage={currentPage} currentStreak={currentStreak} />
      <div className="bdg-page">
        <div className="bdg-header">
          <button className="bkb" onClick={() => nav("dashboard")}>← Back</button>
          <div className="bdg-title-row">
            <h1>🏅 Badges & Achievements</h1>
            {status === "ready" && (
              <div className="bdg-progress-pill">
                {earned.length} / {badges.length} earned
              </div>
            )}
          </div>
          <p>Collect badges by completing labs, maintaining streaks, and reaching milestones.</p>
        </div>

        {/* Overall progress bar */}
        {status === "ready" && badges.length > 0 && (
          <div className="bdg-overall">
            <div className="bdg-overall-track">
              <div
                className="bdg-overall-fill"
                style={{ width: `${Math.round((earned.length / badges.length) * 100)}%` }}
              />
            </div>
            <span className="bdg-overall-pct">
              {Math.round((earned.length / badges.length) * 100)}% complete
            </span>
          </div>
        )}

        {/* Filters */}
        <div className="bdg-filters">
          {[["all", "All"], ["earned", `Earned (${earned.length})`], ["locked", `Locked (${locked.length})`]].map(([v, l]) => (
            <button
              key={v}
              className={`fl${filter === v ? " act" : ""}`}
              onClick={() => setFilter(v)}
            >
              {l}
            </button>
          ))}
        </div>

        {status === "loading" && (
          <div style={{ display: "flex", justifyContent: "center", padding: 60 }}>
            <InlineLoader />
          </div>
        )}

        {status === "error" && (
          <div className="bdg-error">Failed to load badges. Try again later.</div>
        )}

        {status === "ready" && Object.entries(groups).map(([cat, items]) => (
          <div key={cat} className="bdg-group">
            <h2 className="bdg-group-title">
              {CATEGORY_LABEL[cat] || cat}
              <span className="bdg-group-count">{items.filter((b) => b.earned).length}/{items.length}</span>
            </h2>
            <div className="bdg-grid">
              {items.map((b) => (
                <BadgeDetail key={b.badge_id} badge={b} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
