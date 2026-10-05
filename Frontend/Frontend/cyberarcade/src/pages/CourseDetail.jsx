import { useEffect, useState } from "react";
import Navbar from "../components/layout/Navbar";
import I from "../components/icons/Icons";
import { coursesService } from "../services/courses.service";
import { scenariosService } from "../services/scenarios.service";
import { capitalize } from "../utils/helpers";
import { InlineLoader } from "../components/ui/Loader";

const ENV_BADGE = {
  none:      { icon: "📋", label: "Theory",         color: "#555" },
  terminal:  { icon: "⌨️",  label: "Terminal",       color: "#00ff66" },
  dual:      { icon: "⚔️",  label: "Dual Terminal",  color: "#f59e0b" },
  "df-kali": { icon: "🔬",  label: "Forensics Kali", color: "#a78bfa" },
};

const isUUID = (id) =>
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id || "");

const inferEnvRequirement = (lab) => {
  if (!lab) return "none";
  if (lab.env_requirement) return lab.env_requirement;
  const slug = lab.docker_compose_config?.runtime_slug;
  if (slug === "df-kali") return "df-kali";
  if (slug === "ssh-bruteforce") return "dual";
  if (slug) return "terminal";
  return "none";
};

export default function CourseDetail({ theme, setTheme, user, course, nav, onLogout, currentPage, currentStreak }) {
  const [labs, setLabs]     = useState([]);
  const [detail, setDetail] = useState(null);
  const [status, setStatus] = useState("loading");
  const [error, setError]   = useState("");
  const [progress, setProgress] = useState({ lab_statuses: {}, percent: 0, completed_labs: 0, total_labs: 0 });

  useEffect(() => {
    if (!course?.course_id) return;
    let cancelled = false;
    setStatus("loading");
    const scenarioLabs    = scenariosService.labsByCategory(course.category);
    const isScenarioCourse = scenarioLabs.length > 0;

    if (!isUUID(course.course_id)) {
      setDetail(course);
      setLabs(scenarioLabs);
      setStatus("ready");
      return;
    }

    Promise.all([
      coursesService.detail(course.course_id),
      coursesService.labs(course.course_id),
    ])
      .then(([d, l]) => {
        if (cancelled) return;
        setDetail(d);
        setLabs(l || []);
        setStatus("ready");
      })
      .catch((e) => {
        if (cancelled) return;
        if (isScenarioCourse) { setDetail(course); setLabs(scenarioLabs); setStatus("ready"); return; }
        if (e.status === 404 || /not found/i.test(e.message || "")) { nav("courses"); return; }
        setError(e.message || "Failed to load course");
        setStatus("error");
      });

    return () => { cancelled = true; };
  }, [course]);

  useEffect(() => {
    if (!course?.course_id || !isUUID(course.course_id)) return;
    let cancelled = false;
    coursesService.myProgress(course.course_id)
      .then((p) => { if (!cancelled) setProgress(p); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [course]);

  if (!course) return null;
  const scenarioLabs     = scenariosService.labsByCategory(course.category);
  const isScenarioCourse = scenarioLabs.length > 0;
  const view             = detail || course;

  const completed  = progress.completed_labs ?? 0;
  const total      = progress.total_labs     ?? labs.length;
  const remaining  = Math.max(0, total - completed);
  const pct        = progress.percent        ?? 0;

  const getLabStatus = (lb) => progress.lab_statuses?.[lb.lab_id] || null;

  return (
    <div className="pg">
      <Navbar theme={theme} setTheme={setTheme} user={user} nav={nav} onLogout={onLogout} currentPage={currentPage} currentStreak={currentStreak} />
      <div className="cdp">
        <button className="bkb" onClick={() => nav("courses")}><I.Left /> Back to Courses</button>

        {/* Course header */}
        <div className="cdh">
          <span className={`df d-${view.difficulty_level || "beginner"}`}>{capitalize(view.difficulty_level || "")}</span>
          <h1>{view.title}</h1>
          <p>{view.description?.replace(/\s*\[SEED-DATA\].*$/, "")}</p>
          <div className="course-detail-stats">
            <div className="stat-pill"><I.Layers /><span>{labs.length} {labs.length === 1 ? "Lab" : "Labs"}</span></div>
            <div className="stat-pill"><I.Clock /><span>{view.estimated_hours ?? "—"}h estimated</span></div>
            <div className="stat-pill"><I.Hash /><span>{view.category}</span></div>
          </div>
        </div>

        {status === "error" && <div className="ae" style={{ marginBottom: 16 }}>{error}</div>}
        {status === "loading" && <div style={{ display:"flex",justifyContent:"center",padding:40 }}><InlineLoader /></div>}

        {status === "ready" && (
          <>
            {/* Progress stats — only shown for DB courses with progress data */}
            {total > 0 && (
              <div className="prog-stats-grid">
                <div className="prog-stat-card prog-stat-done">
                  <div className="prog-stat-icon">✓</div>
                  <div className="prog-stat-num">{completed}</div>
                  <div className="prog-stat-label">Completed</div>
                </div>
                <div className="prog-stat-card prog-stat-remain">
                  <div className="prog-stat-icon">◎</div>
                  <div className="prog-stat-num">{remaining}</div>
                  <div className="prog-stat-label">Remaining</div>
                </div>
                <div className="prog-stat-card prog-stat-pct">
                  <div className="prog-stat-num">{pct}%</div>
                  <div className="prog-stat-label">Complete</div>
                </div>
              </div>
            )}

            {/* Animated progress bar */}
            {total > 0 && (
              <div className="prog-bar-wrap">
                <div className="prog-bar-track">
                  <div className="prog-bar-fill" style={{ width: `${pct}%` }} />
                </div>
                <div className="prog-bar-meta">
                  <span>{completed} of {total} labs completed</span>
                  <span style={{ color: pct === 100 ? "var(--success)" : "var(--text-muted)" }}>
                    {pct === 100 ? "🎉 Course Complete!" : `${remaining} remaining`}
                  </span>
                </div>
              </div>
            )}

            {/* Learning Path */}
            <h2 className="ssm" style={{ marginTop: 8 }}>Learning Path</h2>
            {labs.length === 0 ? (
              <div className="empty-state"><p>This course has no labs yet.</p></div>
            ) : (
              <div className="lpath">
                {labs.map((lb, i) => {
                  const labStatus = getLabStatus(lb);
                  const isDone    = labStatus === "completed";
                  const isActive  = labStatus === "in_progress";
                  const env       = inferEnvRequirement(lb);
                  const envBadge  = ENV_BADGE[env] || ENV_BADGE.none;

                  return (
                    <div key={lb.lab_id} className="lpath-item" style={{ animationDelay: `${i * 0.06}s` }}>
                      {/* Left: dot + connector */}
                      <div className="lpath-left">
                        <div className={`lpath-dot lpath-dot-${isDone ? "done" : isActive ? "active" : "upcoming"}`}>
                          {isDone ? <I.Check /> : i + 1}
                        </div>
                        {i < labs.length - 1 && (
                          <div className={`lpath-line ${isDone ? "lpath-line-done" : "lpath-line-gray"}`} />
                        )}
                      </div>

                      {/* Right: lab card */}
                      <div
                        className={`lpath-card${isDone ? " lpath-card-done" : isActive ? " lpath-card-active" : ""}`}
                        onClick={() => nav("lab", {
                          lab: { ...lb, courseTitle: view.title, courseCategory: view.category, labIndex: i, totalLabs: labs.length },
                        })}
                      >
                        <div className="lpath-card-body">
                          <div className="lpath-lab-num">Lab {String(i + 1).padStart(2, "0")}</div>
                          <h3>{lb.title}</h3>
                          <div className="lpath-tags">
                            <span className={`df d-${lb.difficulty}`}>{capitalize(lb.difficulty)}</span>
                            <span className="lpath-tag" style={{ color: envBadge.color, borderColor: `${envBadge.color}44` }}>
                              {envBadge.icon} {envBadge.label}
                            </span>
                            {lb.has_auto_solve && (
                              <span className="lpath-tag" style={{ color:"#a78bfa", borderColor:"rgba(167,139,250,.3)" }}>
                                <I.Zap /> Auto-Solve
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="lpath-card-action">
                          {isDone ? (
                            <span className="lpath-badge lpath-badge-done">✓ Done</span>
                          ) : isActive ? (
                            <span className="lpath-badge lpath-badge-active">▶ Continue</span>
                          ) : (
                            <button className="lpath-start-btn">Start <I.Right /></button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
