import { useEffect, useState } from "react";
import Navbar from "../components/layout/Navbar";
import I from "../components/icons/Icons";
import { coursesService } from "../services/courses.service";
import { classesService } from "../services/classes.service";
import { gamificationService } from "../services/gamification.service";
import { capitalize } from "../utils/helpers";
import { InlineLoader } from "../components/ui/Loader";
import { FAKE_COURSES } from "../data/fakeCourses";
import BadgeCard from "../components/gamification/BadgeCard";
import ActivityHeatmap from "../components/gamification/ActivityHeatmap";

const isUUID = (id) =>
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id || "");

// ── Mini leaderboard inside XP panel ──────────────────────────────────────
function MiniLeaderboard({ entries = [], currentUser, onViewAll }) {
  if (!entries.length) return null;
  return (
    <div className="da-mlb">
      <div className="da-mlb-hdr">
        <span className="da-mlb-title">Top Players</span>
        <button className="da-mlb-all" onClick={onViewAll}>Full Board →</button>
      </div>
      {entries.slice(0, 5).map((e, i) => {
        const isMe = e.user_id === String(currentUser?.user_id) ||
                     e.full_name === currentUser?.full_name;
        const medals = ["🥇", "🥈", "🥉"];
        return (
          <div key={e.user_id} className={`da-mlb-row${isMe ? " da-mlb-me" : ""}`}>
            <span className="da-mlb-rank">{medals[i] || `#${i + 1}`}</span>
            <div className="da-mlb-avatar">{e.full_name?.charAt(0)?.toUpperCase()}</div>
            <span className="da-mlb-name">{isMe ? "You" : (e.full_name?.split(" ")[0] || "—")}</span>
            <span className="da-mlb-xp">{(e.total_xp || 0).toLocaleString()} XP</span>
          </div>
        );
      })}
    </div>
  );
}

// ── Mini 14-day activity calendar inside streak panel ─────────────────────
function MiniCalendar({ activity = [] }) {
  const today = new Date();
  const days = [];
  for (let i = 13; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    const key = d.toISOString().split("T")[0];
    const item = activity.find((a) => a.date === key);
    days.push({ date: key, count: item?.count || 0, day: d.getDate() });
  }
  return (
    <div className="da-mcal">
      {days.map((d) => (
        <div
          key={d.date}
          className={`da-mcal-cell${d.count > 0 ? " da-mcal-active" : ""}`}
          title={`${d.date}: ${d.count} activities`}
        >
          <span className="da-mcal-num">{d.day}</span>
        </div>
      ))}
    </div>
  );
}

// ── Main Dashboard component ───────────────────────────────────────────────
export default function Dashboard({ theme, setTheme, user, nav, onLogout, currentPage, userPlan, currentStreak }) {
  const [courses, setCourses]               = useState([]);
  const [enrolledClasses, setEnrolledClasses] = useState([]);
  const [status, setStatus]                 = useState("loading");
  const [progressMap, setProgressMap]       = useState({});
  const [gami, setGami]                     = useState(null);
  const [gamiStatus, setGamiStatus]         = useState("loading");
  const [leaderboard, setLeaderboard]       = useState([]);

  useEffect(() => {
    let cancelled = false;

    Promise.all([
      coursesService.list({ per_page: 50 }).catch(() => []),
      classesService.enrolled().catch(() => []),
    ]).then(([crs, cls]) => {
      if (cancelled) return;
      const real = (crs || []).filter((c) => isUUID(c.course_id));
      const realTitles = new Set(real.map((c) => c.title));
      const extras = FAKE_COURSES.filter((c) => !realTitles.has(c.title));
      setCourses([...real, ...extras]);
      setEnrolledClasses(cls || []);
      setStatus("ready");

      Promise.all(
        real.map((c) =>
          coursesService.myProgress(c.course_id)
            .then((p) => ({ id: c.course_id, data: p }))
            .catch(() => ({ id: c.course_id, data: null }))
        )
      ).then((results) => {
        if (cancelled) return;
        const map = {};
        results.forEach((r) => { if (r.data) map[r.id] = r.data; });
        setProgressMap(map);
      });
    }).catch(() => { if (!cancelled) setStatus("error"); });

    gamificationService.dashboard()
      .then((d) => { if (!cancelled) { setGami(d); setGamiStatus("ready"); } })
      .catch(() => { if (!cancelled) setGamiStatus("error"); });

    gamificationService.leaderboard(10)
      .then((d) => { if (!cancelled) setLeaderboard(d?.entries || []); })
      .catch(() => {});

    return () => { cancelled = true; };
  }, []);

  // ── Derived values ────────────────────────────────────────────────────
  const isPremium = userPlan === "premium";
  const totalLabsDone = Object.values(progressMap).reduce((s, p) => s + (p?.completed_labs || 0), 0);
  const totalLabsAll  = Object.values(progressMap).reduce((s, p) => s + (p?.total_labs || 0), 0);
  const overallPct    = totalLabsAll > 0 ? Math.round((totalLabsDone / totalLabsAll) * 100) : 0;

  const courseHasStarted = (p) =>
    Object.values(p?.lab_statuses || {}).some((s) => s === "in_progress" || s === "completed");
  const continueCourses = courses
    .filter((c) => isUUID(c.course_id))
    .map((c) => ({ ...c, prog: progressMap[c.course_id] }))
    .filter((c) => courseHasStarted(c.prog));

  const openClassCourse = (cls) => {
    const course = courses.find((c) => c.course_id === cls.course_id) || {
      course_id: cls.course_id, title: cls.name, description: cls.description, difficulty_level: "beginner",
    };
    nav("course-detail", { course: { ...course, class_id: cls.class_id, class_name: cls.name } });
  };

  const recentBadges = (gami?.badges || [])
    .sort((a, b) => new Date(b.awarded_at) - new Date(a.awarded_at))
    .slice(0, 6);

  const xp      = gami?.xp      || {};
  const streak  = gami?.streak  || {};

  // ── Render ─────────────────────────────────────────────────────────────
  return (
    <div className="pg">
      <Navbar theme={theme} setTheme={setTheme} user={user} nav={nav} onLogout={onLogout} currentPage={currentPage} currentStreak={currentStreak} />
      <div className="da2-page">

        {/* ══ WELCOME HEADER ════════════════════════════════════════════ */}
        <div className="da2-welcome">
          <div className="da2-welcome-text">
            <h1 className="da2-welcome-h">
              Welcome back, <span className="he">{user?.full_name?.split(" ")[0] || "Agent"}</span>
            </h1>
            <p className="da2-welcome-sub">
              Your cybersecurity command center — track progress, collect badges, and level up your skills
            </p>
          </div>
          {!isPremium && (
            <div className="da2-upgrade-pill" onClick={() => nav("subscription")}>
              <I.Crown /> Upgrade to Premium
            </div>
          )}
        </div>

        {/* ══ TOP 3 STAT CARDS ══════════════════════════════════════════ */}
        <div className="da2-top-stats">
          <div className="da2-top-stat da2-ts-labs">
            <div className="da2-ts-v">{gamiStatus === "ready" ? (gami?.labs_completed ?? 0) : "—"}</div>
            <div className="da2-ts-l">Labs Completed</div>
          </div>
          <div className="da2-top-stat da2-ts-tasks">
            <div className="da2-ts-v">{gamiStatus === "ready" ? (gami?.tasks_completed ?? 0) : "—"}</div>
            <div className="da2-ts-l">Tasks Done</div>
          </div>
          <div className="da2-top-stat da2-ts-courses">
            <div className="da2-ts-v">{gamiStatus === "ready" ? (gami?.courses_completed ?? 0) : "—"}</div>
            <div className="da2-ts-l">Courses Done</div>
          </div>
        </div>

        {/* ══ TWO-COLUMN BODY ═══════════════════════════════════════════ */}
        <div className="da2-body">

          {/* ── LEFT: Main content ─────────────────────────────────── */}
          <div className="da2-main">

            {/* Overall learning progress */}
            {totalLabsAll > 0 && (
              <div className="da2-card da2-prog-card">
                <div className="da2-card-hdr">
                  <span className="da2-card-title">Overall Progress</span>
                  <span className="da2-prog-badge">{totalLabsDone}/{totalLabsAll} labs · {overallPct}%</span>
                </div>
                <div className="da2-prog-track">
                  <div className="da2-prog-fill" style={{ width: `${overallPct}%` }} />
                </div>
              </div>
            )}

            {/* Enrolled classes */}
            {enrolledClasses.length > 0 && (
              <div className="da2-section">
                <h2 className="da2-section-title">Your Classes</h2>
                <div className="cg">
                  {enrolledClasses.slice(0, 3).map((cls) => (
                    <div key={cls.class_id} className="cc" onClick={() => openClassCourse(cls)}>
                      <div className="ct">
                        <span className="cp">{cls.name}</span>
                        <span className={cls.is_active ? "adm-pub-yes" : "adm-pub-no"}>
                          {cls.is_active ? "Active" : "Ended"}
                        </span>
                      </div>
                      {cls.description && <p>{cls.description}</p>}
                      <button className="btn ba2 bs" style={{ marginTop: 12 }}>
                        Open Course <I.Right />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Continue learning */}
            {status === "ready" && continueCourses.length > 0 && (
              <div className="da2-section">
                <h2 className="da2-section-title">Continue Learning</h2>
                <div className="dash-continue-grid">
                  {continueCourses.map((c) => {
                    const pct  = c.prog?.percent        ?? 0;
                    const done = c.prog?.completed_labs ?? 0;
                    const tot  = c.prog?.total_labs     ?? (c.lab_count ?? 0);
                    return (
                      <div key={c.course_id} className="dash-course-card" onClick={() => nav("course-detail", { course: c })}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                          <div>
                            <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "1.5px", color: "var(--accent-bright)", marginBottom: 6 }}>{c.category}</div>
                            <div style={{ fontSize: 15, fontWeight: 700 }}>{c.title}</div>
                          </div>
                          <span className={`df d-${c.difficulty_level}`} style={{ flexShrink: 0 }}>{capitalize(c.difficulty_level)}</span>
                        </div>
                        {tot > 0 && (
                          <>
                            <div className="prog-bar-track" style={{ height: 5 }}>
                              <div className="prog-bar-fill" style={{ width: `${pct}%` }} />
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--text-muted)" }}>
                              <span>{done}/{tot} labs</span>
                              <span style={{ fontWeight: 700, color: pct > 0 ? "var(--accent-bright)" : "var(--text-muted)" }}>{pct}%</span>
                            </div>
                          </>
                        )}
                        <div style={{ alignSelf: "flex-end" }}>
                          <button className="btn ba2 bs">{done > 0 ? "Continue →" : "Start →"}</button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Recent achievements */}
            {recentBadges.length > 0 && (
              <div className="da2-section">
                <div className="da2-section-hdr">
                  <h2 className="da2-section-title">Recent Achievements</h2>
                  <button className="btn bg bs" onClick={() => nav("badges")}>View All</button>
                </div>
                <div className="gami-badges-row">
                  {recentBadges.map((b) => (
                    <BadgeCard key={b.badge_id} badge={b} />
                  ))}
                </div>
              </div>
            )}

            {/* Activity heatmap */}
            {gamiStatus === "ready" && (gami?.activity || []).length > 0 && (
              <div className="da2-card">
                <div className="da2-card-title" style={{ marginBottom: 14 }}>Activity</div>
                <ActivityHeatmap activity={gami.activity} />
              </div>
            )}

            {/* All courses */}
            <div className="da2-section">
              <div className="da2-section-hdr">
                <h2 className="da2-section-title">All Courses</h2>
                <button className="btn bg bs" onClick={() => nav("courses")}>Browse All</button>
              </div>
              {status === "loading" && (
                <div style={{ display: "flex", justifyContent: "center", padding: 32 }}>
                  <InlineLoader />
                </div>
              )}
              {status === "ready" && courses.length === 0 && (
                <div style={{ padding: 32, textAlign: "center", color: "var(--text-muted)", border: "1px dashed var(--border)", borderRadius: 12 }}>
                  No published courses yet.
                </div>
              )}
              {status === "ready" && courses.length > 0 && (
                <div className="cg">
                  {courses.slice(0, 6).map((c) => {
                    const prog = progressMap[c.course_id];
                    const pct  = prog?.percent        ?? 0;
                    const done = prog?.completed_labs ?? 0;
                    const tot  = prog?.total_labs     ?? 0;
                    return (
                      <div key={c.course_id} className="cc" onClick={() => nav("course-detail", { course: c })}>
                        <div className="ct">
                          <span className={`df d-${c.difficulty_level}`}>{capitalize(c.difficulty_level)}</span>
                          <span className="cp">{c.category}</span>
                        </div>
                        <h3>{c.title}</h3>
                        <p>{c.description?.slice(0, 90)}{c.description?.length > 90 ? "…" : ""}</p>
                        {tot > 0 && (
                          <div style={{ marginTop: "auto" }}>
                            <div className="pb" style={{ marginBottom: 6 }}>
                              <div className="pf" style={{ width: `${pct}%` }} />
                            </div>
                            <div style={{ fontSize: 11, color: "var(--text-muted)", display: "flex", justifyContent: "space-between" }}>
                              <span>{done}/{tot} labs</span><span>{pct}%</span>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

          </div>

          {/* ── RIGHT: Sidebar panels ──────────────────────────────── */}
          <div className="da2-sidebar">

            {/* XP / Level panel — TryHackMe style */}
            <div className="da2-xp-panel">
              <div className="da2-xp-panel-hdr">
                <span className="da2-xp-panel-title">Your Stats</span>
                <button className="da2-xp-profile-btn" onClick={() => nav("profile")}>Go to profile</button>
              </div>

              <div className="da2-xp-user">
                <div className="da2-xp-avatar">
                  {user?.full_name?.charAt(0)?.toUpperCase() || "?"}
                </div>
                <div className="da2-xp-user-info">
                  <div className="da2-xp-username">
                    {user?.full_name?.split(" ")[0]}
                    <span className="da2-xp-rank-tag"> [{(xp.level_title || "Recruit").toUpperCase()}]</span>
                  </div>
                  <div className="da2-xp-level-row">
                    <span className="da2-xp-level-lbl">Level {xp.current_level || 1}</span>
                    <div className="da2-xp-bar-track">
                      <div className="da2-xp-bar-fill" style={{ width: `${xp.progress_pct || 0}%` }}>
                        {(xp.progress_pct || 0) > 4 && <span className="da2-xp-bolt">⚡</span>}
                      </div>
                    </div>
                    <span className="da2-xp-hex">[0x{(xp.current_level || 1).toString(16)}]</span>
                  </div>
                  <div className="da2-xp-sub">
                    {(xp.total_xp || 0).toLocaleString()} XP
                    {xp.xp_to_next_level > 0 && <span> · {xp.xp_to_next_level} to next</span>}
                  </div>
                </div>
              </div>

              <MiniLeaderboard entries={leaderboard} currentUser={user} onViewAll={() => nav("leaderboard")} />
            </div>


            {/* Daily streak widget */}
            <div className="da2-streak-panel">
              <div className="da2-sw-header">
                <span className="da2-sw-label">DAILY STREAK</span>
                <span className="da2-sw-ice">❄️</span>
              </div>
              <div className="da2-sw-main">
                <span className="da2-sw-count">{streak.current_streak || 0}</span>
                <span className="da2-sw-unit">days</span>
              </div>
              <div className="da2-sw-divider" />
              <div className="da2-sw-stats">
                <div className="da2-sw-stat">
                  <span className="da2-sw-stat-val">{streak.longest_streak || 0}</span>
                  <span className="da2-sw-stat-lbl">BEST</span>
                </div>
                <div className="da2-sw-stat">
                  <span className="da2-sw-stat-val">{streak.total_active_days || 0}</span>
                  <span className="da2-sw-stat-lbl">TOTAL DAYS</span>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}
